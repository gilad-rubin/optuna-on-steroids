# File: magic.py

from pathlib import Path
from typing import Any, Dict, List

import ipywidgets as widgets
import pandas as pd
from IPython.core.magic import Magics, cell_magic, magics_class
from IPython.core.magic_arguments import argument, magic_arguments, parse_argstring
from IPython.display import HTML, clear_output, display

from .core import Hypster, find_hp_function_body_and_name
from .hp import HP
from .selection_handler import SelectionHandler


def custom_load(module_source: str, inject_names=True) -> Hypster:
    """
    Custom loader to parse the configuration module source code.

    Args:
        module_source (str): The source code of the configuration module.
        inject_names (bool): Whether to inject variable names into the namespace.

    Returns:
        Hypster: An instance of the Hypster configuration.
    """
    module_source = module_source.replace("@config", "").replace("@hypster.config", "")
    namespace = {"HP": HP}
    exec(module_source, namespace)
    result = find_hp_function_body_and_name(module_source)

    if result is None:
        raise ValueError("No configuration function found in the module")

    func_name, config_body = result
    func = namespace.get(func_name)

    if func is None:
        raise ValueError(f"Could not find the function {func_name} in the loaded module")

    return Hypster(func_name, config_body, namespace, inject_names)


class InteractiveHypster:
    """
    Interactive UI for Hypster configurations using ipywidgets.
    """

    def __init__(
        self,
        hp_config: Hypster,
        shell,
        selections: Dict[str, Any] = None,
        overrides: Dict[str, Any] = None,
        final_vars: List[str] = None,
        results_var: str = None,
        instantiate_on_first: bool = False,
        instantiate_on_change: bool = False,
    ):
        self.hp_config = hp_config
        self.shell = shell
        self.selection_handler = SelectionHandler(hp_config)
        self.selection_handler.initialize()
        self.overrides = overrides or {}
        self.final_vars = final_vars or []
        self.results_var = results_var
        self.instantiate_on_first = instantiate_on_first
        self.instantiate_on_change = instantiate_on_change
        self.widgets = {}
        self.output = widgets.Output()
        self.widgets_container = widgets.VBox([])
        self.create_widgets()
        self.update_widgets_display()
        if self.instantiate_on_first:
            self.instantiate(None)

    def create_widgets(self):
        """
        Create widgets based on the current state of selections.
        """
        state = self.selection_handler.get_current_state()
        # Iterate in the order of selected_params to maintain widget order
        for param in state["selected_params"]:
            if param in state["current_options"]:
                options = state["current_options"][param]
                value = state["selected_params"][param]
                self.create_widget_for_param(param, options, value)

    def create_widget_for_param(self, param, options, value):
        """
        Create a widget for a given parameter based on its type.

        Args:
            param (str): The parameter name.
            options (Any): The options available for the parameter.
            value (Any): The current value of the parameter.
        """
        if param in self.overrides:
            value = self.overrides[param]
            disabled = True
        else:
            disabled = False

        if isinstance(options, dict):
            widget = self.create_dict_widget(param, options, value)
        elif isinstance(value, list):
            widget = self.create_list_widget(param, options, value)
        else:
            widget = self.create_singular_widget(param, options, value)

        widget.disabled = disabled
        self.widgets[param] = widget

    def create_dict_widget(self, param, options, value):
        """
        Create an accordion widget for dictionary-type parameters.

        Args:
            param (str): The parameter name.
            options (dict): Nested options for the parameter.
            value (dict): The current nested values for the parameter.

        Returns:
            widgets.Accordion: The accordion widget containing sub-widgets.
        """
        sub_widgets = []
        for sub_param, sub_options in options.items():
            sub_value = value.get(sub_param, None)
            sub_widget = self.create_widget_for_param(f"{param}.{sub_param}", sub_options, sub_value)
            sub_widgets.append(sub_widget)

        accordion = widgets.Accordion(children=sub_widgets)
        accordion.set_title(0, param)
        return accordion

    def create_list_widget(self, param, options, value):
        """
        Create a multi-select widget for list-type parameters.

        Args:
            param (str): The parameter name.
            options (set): The available options.
            value (list): The current selected values.

        Returns:
            widgets.SelectMultiple: The multi-select widget.
        """
        widget = widgets.SelectMultiple(
            options=sorted(list(options)),
            value=value,
            description=f"Select {param}",
            style={"description_width": "initial"},
        )
        # Observe changes to the 'value' property
        widget.observe(lambda change: self.on_change_list(param, change["new"]), names="value")
        return widget

    def on_change_list(self, param, new_value):
        """
        Handle changes in multi-select widgets.

        Args:
            param (str): The parameter name.
            new_value (tuple): The new selected values.
        """
        new_value = list(new_value)  # Convert from tuple to list
        # Update the parameter and refresh widgets
        self.selection_handler.update_param(param, new_value)
        self.update_widgets()
        self.display_valid_combinations()

        if self.instantiate_on_change:
            self.instantiate(None)

    def create_singular_widget(self, param, options, value):
        """
        Create a dropdown widget for singular-type parameters.

        Args:
            param (str): The parameter name.
            options (set): The available options.
            value (Any): The current selected value.

        Returns:
            widgets.Dropdown: The dropdown widget.
        """
        widget = widgets.Dropdown(
            options=sorted(list(options)),
            value=value,
            description=f"Select {param}",
            style={"description_width": "initial"},
        )
        # Observe changes to the 'value' property
        widget.observe(lambda change: self.on_change(param, change["new"]), names="value")
        return widget

    def on_change(self, param, new_value):
        """
        Handle changes in singular widgets.

        Args:
            param (str): The parameter name.
            new_value (Any): The new selected value.
        """
        # Update the parameter and refresh widgets
        self.selection_handler.update_param(param, new_value)
        self.update_widgets()
        self.display_valid_combinations()

        if self.instantiate_on_change:
            self.instantiate(None)

    def update_widgets(self):
        """
        Update existing widgets and create/remove widgets based on the current state.
        """
        state = self.selection_handler.get_current_state()
        current_params = set(state["selected_params"].keys())
        existing_params = set(self.widgets.keys())

        # Remove widgets for params that no longer exist
        for param in list(existing_params - current_params):
            del self.widgets[param]

        # Update or create widgets for current params
        for param in state["selected_params"]:
            if param in state["current_options"]:
                options = state["current_options"][param]
                value = state["selected_params"][param]
                if param in self.widgets:
                    self.update_widget(param, options, value)
                else:
                    self.create_widget_for_param(param, options, value)

        self.update_widgets_display()

    def update_widget(self, param, options, value):
        """
        Update an existing widget with new options and values.

        Args:
            param (str): The parameter name.
            options (Any): The updated options.
            value (Any): The updated value.
        """
        widget = self.widgets[param]
        if isinstance(options, dict):
            for sub_param, sub_options in options.items():
                full_param = f"{param}.{sub_param}"
                sub_value = value.get(sub_param, None)
                if full_param in self.widgets:
                    self.update_widget(full_param, sub_options, sub_value)
                else:
                    self.create_widget_for_param(full_param, sub_options, sub_value)
        elif isinstance(widget, widgets.SelectMultiple):
            widget.options = sorted(list(options))
            widget.value = [v for v in value if v in options]
        else:
            sorted_options = sorted(list(options))
            widget.options = sorted_options
            # Ensure the selected value is still valid
            widget.value = value if value in options else sorted_options[0]

    def update_widgets_display(self):
        """
        Refresh the widgets container to reflect the current set of widgets while maintaining order.
        """
        state = self.selection_handler.get_current_state()
        children = []
        # Iterate in the order of 'selected_params' to maintain widget order
        for param in state["selected_params"]:
            if param in self.widgets:
                children.append(self.widgets[param])
        self.widgets_container.children = children

    def display_valid_combinations(self):
        """
        Display the dataframe of valid parameter combinations based on current selections.
        """
        with self.output:
            clear_output(wait=True)
            valid_combinations = self.selection_handler.filtered_combinations
            if valid_combinations:
                df = pd.DataFrame(valid_combinations)
                display(df)

    def instantiate(self, button):
        """
        Instantiate the configuration based on current selections.

        Args:
            button (widgets.Button): The button widget triggering the instantiation.
        """
        with self.output:
            clear_output(wait=True)
            state = self.selection_handler.get_current_state()
            results = self.hp_config(
                final_vars=self.final_vars, selections=state["selected_params"], overrides=self.overrides
            )
            if self.results_var:
                self.shell.user_ns[self.results_var] = results
            else:
                self.shell.user_ns.update(results)

    def display(self):
        """
        Display the interactive widgets and instantiate button in the notebook.
        """
        instantiate_button = widgets.Button(description="Instantiate")
        instantiate_button.on_click(self.instantiate)

        if self.instantiate_on_change:
            button_layout = widgets.Layout(display="none")
        else:
            button_layout = widgets.Layout()

        instantiate_button.layout = button_layout

        display(widgets.VBox([self.widgets_container, instantiate_button, self.output]))


@magics_class
class HypsterMagics(Magics):
    """
    Custom IPython magic for Hypster configurations.
    """

    def __init__(self, shell):
        super().__init__(shell)
        self._first_run = True

    @magic_arguments()
    @argument("config_name", help="Name for the config module")
    @argument("-s", "--selections", help="Variable name containing selections dict")
    @argument("-o", "--overrides", help="Variable name containing overrides dict")
    @argument("-f", "--final_vars", help="Comma-separated list of final variables")
    @argument("-w", "--write_to_file", help="Write cell content to a file")
    @argument("-r", "--results", help="Variable name to store the results dictionary")
    @argument(
        "-i",
        "--instantiate",
        choices=["first", "change", "button", "first,change"],
        help="Instantiation behavior: 'first' (on first run), 'change' (on parameter change), "
        "'button' (manual only), or 'first,change' (on first run and parameter change)",
    )
    @cell_magic
    def hypster(self, line, cell):
        """
        Cell magic to initialize InteractiveHypster with given configuration.

        Usage:
            %%hypster config_name --results results_var -i first,change
            # Configuration code here
        """
        # Inject custom CSS to style the widgets
        css = """
        <style>
        .cell-output-ipywidget-background {
           background-color: transparent !important;
        }
        :root {
            --jp-widgets-color: var(--vscode-editor-foreground);
            --jp-widgets-font-size: var(--vscode-editor-font-size);
        }
        </style>
        """
        display(HTML(css))

        # Parse magic arguments
        args = parse_argstring(self.hypster, line)
        hp_config = custom_load(cell)

        # Retrieve selections and overrides from user namespace
        selections = self.shell.user_ns.get(args.selections, {}) if args.selections else {}
        overrides = self.shell.user_ns.get(args.overrides, {}) if args.overrides else {}
        final_vars = args.final_vars.split(",") if args.final_vars else None
        results_var = args.results

        # Determine instantiation behavior
        instantiate_options = args.instantiate.split(",") if args.instantiate else ["button"]
        instantiate_on_first = "first" in instantiate_options
        instantiate_on_change = "change" in instantiate_options

        # Initialize and display InteractiveHypster
        interactive_hypster = InteractiveHypster(
            hp_config,
            self.shell,
            selections,
            overrides,
            final_vars,
            results_var,
            instantiate_on_first=instantiate_on_first,
            instantiate_on_change=instantiate_on_change,
        )
        interactive_hypster.display()

        # Store the configuration in the user namespace
        self.shell.user_ns[args.config_name] = hp_config

        # Optionally write the configuration to a file
        if args.write_to_file:
            Path(args.write_to_file).write_text(cell)

        return None


def load_ipython_extension(ipython):
    """
    Register the HypsterMagics with IPython.
    """
    ipython.register_magics(HypsterMagics)
