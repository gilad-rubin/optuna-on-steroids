# core.py
import ast
import inspect
import types
from typing import Any, Callable, Dict, List, Optional, Union

from .ast_analyzer import analyze_hp_calls, inject_names
from .logging_utils import configure_logging

logger = configure_logging()

class HP:
    def __init__(self, final_vars: List[str], selections: Dict[str, Any], overrides: Dict[str, Any]):
        self.final_vars = final_vars
        self.selections = selections
        self.overrides = overrides
        self.config_dict = {}
        logger.info("Initialized HP with final_vars: %s, selections: %s, and overrides: %s", 
                    self.final_vars, self.selections, self.overrides)

    def select(self, options: Union[Dict[str, Any], List[Any]], name: str = None, default: Any = None):
        if name is None:
            raise ValueError("Name must be provided explicitly or automatically inferred.")

        if isinstance(options, dict):
            if not all(isinstance(k, str) for k in options.keys()):
                bad_keys = [key for key in options.keys() if not isinstance(key, str)]
                raise ValueError(f"Dictionary keys must be strings. got {bad_keys} instead.")
        elif isinstance(options, list):
            if not all(isinstance(v, (str, int, bool, float)) for v in options):
                raise ValueError("List values must be one of: str, int, bool, float.")
            options = {v: v for v in options}
        else:
            raise ValueError("Options must be a dictionary or a list.")

        if default is not None and default not in options:
            raise ValueError("Default value must be one of the options.")

        logger.debug("Select called with options: %s, name: %s, default: %s", options, name, default)

        result = None
        if name in self.overrides:
            override_value = self.overrides[name]
            logger.debug("Found override for %s: %s", name, override_value)
            if override_value in options:
                result = options[override_value]
            else:
                result = override_value
            logger.info("Applied override for %s: %s", name, result)
        elif name in self.selections:
            selected_value = self.selections[name]
            logger.debug("Found selection for %s: %s", name, selected_value)
            if selected_value in options:
                result = options[selected_value]
                logger.info("Applied selection for %s: %s", name, result)
            else:
                raise InvalidSelectionError(
                    f"Invalid selection '{selected_value}' for '{name}'. Not in options: {list(options.keys())}"
                )
        elif default is not None:
            result = options[default]
        else:
            raise ValueError(f"No selection or override found for {name} and no default provided.")

        self.config_dict[name] = result
        return result

    def text_input(self, default: Optional[str] = None, name: Optional[str] = None) -> str:
        if name is None:
            raise ValueError("Name must be provided explicitly or automatically inferred.")

        logger.debug("Text input called with default: %s, name: %s", default, name)
        
        if name in self.overrides:
            result = self.overrides[name]
        elif default is None:
            raise ValueError(f"No default value or override provided for text input {name}.")
        else:
            result = default
        
        logger.info("Text input for %s: %s", name, result)

        self.config_dict[name] = result
        return result

    def number_input(self, default: Optional[Union[int, float]] = None, name: Optional[str] = None) -> Union[int, float]:
        if name is None:
            raise ValueError("Name must be provided explicitly or automatically inferred.")

        logger.debug("Number input called with default: %s, name: %s", default, name)
        
        if name in self.overrides:
            result = self.overrides[name]
        elif default is None:
            raise ValueError(f"No default value or override provided for number input {name}.")
        else:
            result = default
        
        logger.info("Number input for %s: %s", name, result)

        self.config_dict[name] = result
        return result
    
    def propagate(self, config_func: Callable, name: str) -> Dict[str, Any]:
        logger.info(f"Propagating configuration for {name}")
        
        # Create dictionaries for the nested configuration
        nested_selections = {k[len(name)+1:]: v for k, v in self.selections.items() if k.startswith(f"{name}.")}
        nested_overrides = {k[len(name)+1:]: v for k, v in self.overrides.items() if k.startswith(f"{name}.")}
        
        # Automatically propagate final_vars
        nested_final_vars = [var[len(name)+1:] for var in self.final_vars if var.startswith(f"{name}.")]
        
        logger.debug(f"Propagated configuration for {name} with Selections:\n{nested_selections}\n& Overrides:\n{nested_overrides}\nAuto-propagated final vars: {nested_final_vars}")
        result = config_func(final_vars=nested_final_vars, selections=nested_selections, overrides=nested_overrides)
        
        # Update the config_dict with the propagated results
        self.config_dict[name] = result
        
        return result

class Hypster:
    def __init__(self, func: Callable, source_code: str = None):
        self.func = func
        self.source_code = source_code or inspect.getsource(func)

    def __call__(self, final_vars: List[str] = [], selections: Dict[str, Any] = {}, overrides: Dict[str, Any] = {}):
        logger.info("Hypster called with final_vars: %s, selections: %s, overrides: %s", 
                    final_vars, selections, overrides)
        try:
            hp = HP(final_vars, selections, overrides)

            # Analyze and modify the source code
            results, hp_calls = analyze_hp_calls(self.source_code)
            modified_source = inject_names(self.source_code, hp_calls)
            
            # Extract the function body
            function_body = self._extract_function_body(modified_source)

            # Create a new namespace and add the 'hp' object to it
            namespace = {'hp': hp}

            # Execute the modified function body in this namespace
            exec(function_body, globals(), namespace)

            # Process and filter the results
            final_result = self._process_results(namespace)

            if not final_vars:
                return final_result
            else:
                result = {k: final_result.get(k, None) for k in final_vars}
                logger.debug("Final result after filtering by final_vars: %s", result)
                return result

        except Exception as e:
            logger.error("An error occurred: %s", str(e))
            raise
        
    def save(self, path: str):
        save(self, path)
        
    def _extract_function_body(self, source: str) -> str:
        lines = source.split('\n')
        body_start = next(i for i, line in enumerate(lines) if line.strip().endswith(':'))
        body_lines = lines[body_start + 1:]
        min_indent = min(len(line) - len(line.lstrip()) for line in body_lines if line.strip())
        return '\n'.join(line[min_indent:] for line in body_lines)

    def _process_results(self, namespace: Dict[str, Any]) -> Dict[str, Any]:
        filtered_locals = {
            k: v for k, v in namespace.items()
            if k != 'hp' and not k.startswith('__') and not isinstance(v, (types.ModuleType, types.FunctionType, type))
        }

        final_result = {k: v for k, v in filtered_locals.items() if not k.startswith('_')}

        logger.debug("Captured locals: %s", filtered_locals)
        logger.debug("Final result after filtering: %s", final_result)

        return final_result

def config(func: Callable) -> Hypster:
    return Hypster(func)

def save(hypster_instance: Hypster, path: Optional[str] = None):
    if not isinstance(hypster_instance, Hypster):
        raise ValueError("The provided object is not a Hypster instance")

    if path is None:
        path = f"{hypster_instance.func.__name__}.py"

    # Parse the source code into an AST
    tree = ast.parse(hypster_instance.source_code)

    # Find the function definition and remove decorators
    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef):
            node.decorator_list = []
            break

    # Convert the modified AST back to source code
    modified_source = ast.unparse(tree)

    with open(path, "w") as f:
        f.write(modified_source)

    logger.info("Configuration saved to %s", path)

def load(path: str) -> Hypster:
    with open(path, "r") as f:
        source = f.read()

    # Execute the source code to define the function
    namespace = {}
    exec(source, namespace)

    # Find the function in the namespace
    for name, obj in namespace.items():
        if callable(obj) and not name.startswith("__"):
            # Create and return a Hypster instance with the source code
            return Hypster(obj, source_code=source)

    raise ValueError("No suitable function found in the source code")

class InvalidSelectionError(Exception):
    pass