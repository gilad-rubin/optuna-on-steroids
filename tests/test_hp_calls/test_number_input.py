import pytest

from hypster import HP, config


# Number Input Tests
def test_number_input_with_default():
    @config
    def config_func(hp: HP):
        value = hp.number_input(default=0.5, name="param")

    result = config_func()
    assert result["value"] == 0.5


def test_number_input_without_default():
    with pytest.raises(TypeError):

        @config
        def config_func(hp: HP):
            value = hp.number_input(name="param")

        config_func()


def test_number_input_invalid_default():
    with pytest.raises(TypeError):

        @config
        def config_func(hp: HP):
            value = hp.number_input(default="not a number", name="param")

        config_func()


def test_number_input_with_override():
    @config
    def config_func(hp: HP):
        value = hp.number_input(default=0.5, name="param")

    result = config_func(overrides={"param": 1.5})
    assert result["value"] == 1.5


def test_number_input_invalid_override():
    @config
    def config_func(hp: HP):
        value = hp.number_input(default=0.5, name="param")

    with pytest.raises(TypeError):
        config_func(overrides={"param": "not a number"})


# Multi Number Tests
def test_multi_number_with_default():
    @config
    def config_func(hp: HP):
        values = hp.multi_number(default=[1.0, 2.0], name="param")

    result = config_func()
    assert result["values"] == [1.0, 2.0]


def test_multi_number_without_default():
    @config
    def config_func(hp: HP):
        values = hp.multi_number(name="param")

    result = config_func()
    assert result["values"] == []


def test_multi_number_invalid_default():
    with pytest.raises(TypeError):

        @config
        def config_func(hp: HP):
            values = hp.multi_number(default=["a", "b"], name="param")  # Not numbers

        config_func()


def test_multi_number_with_override():
    @config
    def config_func(hp: HP):
        values = hp.multi_number(default=[1.0, 2.0], name="param")

    result = config_func(overrides={"param": [3.0, 4.0]})
    assert result["values"] == [3.0, 4.0]


def test_multi_number_invalid_override_type():
    @config
    def config_func(hp: HP):
        values = hp.multi_number(default=[1.0, 2.0], name="param")

    with pytest.raises(TypeError):
        config_func(overrides={"param": 3.0})  # Not a list


def test_multi_number_invalid_override():
    @config
    def config_func(hp: HP):
        values = hp.multi_number(default=[1.0, 2.0], name="param")

    with pytest.raises(TypeError):
        config_func(overrides={"param": ["a", "b"]})  # Not numbers


# Min/Max validation tests for number_input
def test_number_input_with_min():
    @config
    def config_func(hp: HP):
        value = hp.number_input(default=0.5, min=0.0, name="param")

    result = config_func()
    assert result["value"] == 0.5


def test_number_input_with_max():
    @config
    def config_func(hp: HP):
        value = hp.number_input(default=0.5, max=1.0, name="param")

    result = config_func()
    assert result["value"] == 0.5


def test_number_input_with_min_max():
    @config
    def config_func(hp: HP):
        value = hp.number_input(default=0.5, min=0.0, max=1.0, name="param")

    result = config_func()
    assert result["value"] == 0.5


def test_number_input_default_below_min():
    with pytest.raises(ValueError):

        @config
        def config_func(hp: HP):
            value = hp.number_input(default=-0.1, min=0.0, name="param")

        config_func()


def test_number_input_default_above_max():
    with pytest.raises(ValueError):

        @config
        def config_func(hp: HP):
            value = hp.number_input(default=1.1, max=1.0, name="param")

        config_func()


def test_number_input_override_below_min():
    @config
    def config_func(hp: HP):
        value = hp.number_input(default=0.5, min=0.0, name="param")

    with pytest.raises(ValueError):
        config_func(overrides={"param": -0.1})


def test_number_input_override_above_max():
    @config
    def config_func(hp: HP):
        value = hp.number_input(default=0.5, max=1.0, name="param")

    with pytest.raises(ValueError):
        config_func(overrides={"param": 1.1})


# Min/Max validation tests for multi_number
def test_multi_number_with_min():
    @config
    def config_func(hp: HP):
        values = hp.multi_number(default=[0.5, 0.6], min=0.0, name="param")

    result = config_func()
    assert result["values"] == [0.5, 0.6]


def test_multi_number_with_max():
    @config
    def config_func(hp: HP):
        values = hp.multi_number(default=[0.5, 0.6], max=1.0, name="param")

    result = config_func()
    assert result["values"] == [0.5, 0.6]


def test_multi_number_with_min_max():
    @config
    def config_func(hp: HP):
        values = hp.multi_number(default=[0.5, 0.6], min=0.0, max=1.0, name="param")

    result = config_func()
    assert result["values"] == [0.5, 0.6]


def test_multi_number_default_below_min():
    with pytest.raises(ValueError):

        @config
        def config_func(hp: HP):
            values = hp.multi_number(default=[0.5, -0.1], min=0.0, name="param")

        config_func()


def test_multi_number_default_above_max():
    with pytest.raises(ValueError):

        @config
        def config_func(hp: HP):
            values = hp.multi_number(default=[0.5, 1.1], max=1.0, name="param")

        config_func()


def test_multi_number_override_below_min():
    @config
    def config_func(hp: HP):
        values = hp.multi_number(default=[0.5, 0.6], min=0.0, name="param")

    with pytest.raises(ValueError):
        config_func(overrides={"param": [0.5, -0.1]})


def test_multi_number_override_above_max():
    @config
    def config_func(hp: HP):
        values = hp.multi_number(default=[0.5, 0.6], max=1.0, name="param")

    with pytest.raises(ValueError):
        config_func(overrides={"param": [0.5, 1.1]})
