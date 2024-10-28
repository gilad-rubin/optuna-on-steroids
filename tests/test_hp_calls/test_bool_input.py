import pytest

from hypster import HP, config


# Bool Input Tests
def test_bool_input_with_default():
    @config
    def config_func(hp: HP):
        value = hp.bool_input(default=True, name="param")

    result = config_func()
    assert result["value"] is True
    assert isinstance(result["value"], bool)


def test_bool_input_without_default():
    with pytest.raises(TypeError):

        @config
        def config_func(hp: HP):
            value = hp.bool_input(name="param")

        config_func()


def test_bool_input_invalid_default():
    with pytest.raises(TypeError):

        @config
        def config_func(hp: HP):
            value = hp.bool_input(default="true", name="param")  # Not a boolean

        config_func()


def test_bool_input_with_override():
    @config
    def config_func(hp: HP):
        value = hp.bool_input(default=True, name="param")

    result = config_func(overrides={"param": False})
    assert result["value"] is False
    assert isinstance(result["value"], bool)


def test_bool_input_invalid_override():
    @config
    def config_func(hp: HP):
        value = hp.bool_input(default=True, name="param")

    with pytest.raises(TypeError):
        config_func(overrides={"param": "true"})  # Not a boolean


# Multi Bool Tests
def test_multi_bool_with_default():
    @config
    def config_func(hp: HP):
        values = hp.multi_bool(default=[True, False], name="param")

    result = config_func()
    assert result["values"] == [True, False]
    assert all(isinstance(x, bool) for x in result["values"])


def test_multi_bool_without_default():
    @config
    def config_func(hp: HP):
        values = hp.multi_bool(name="param")

    results = config_func()
    assert results["values"] == []


def test_multi_bool_invalid_default():
    with pytest.raises(TypeError):

        @config
        def config_func(hp: HP):
            values = hp.multi_bool(default=[True, "false"], name="param")  # Not all booleans

        config_func()


def test_multi_bool_with_override():
    @config
    def config_func(hp: HP):
        values = hp.multi_bool(default=[True, True], name="param")

    result = config_func(overrides={"param": [False, False]})
    assert result["values"] == [False, False]


def test_multi_bool_invalid_override():
    @config
    def config_func(hp: HP):
        values = hp.multi_bool(default=[True, False], name="param")

    with pytest.raises(TypeError):
        config_func(overrides={"param": [True, "false"]})  # Not all booleans


def test_multi_bool_invalid_override_type():
    @config
    def config_func(hp: HP):
        values = hp.multi_bool(default=[True, False], name="param")

    with pytest.raises(TypeError):
        config_func(overrides={"param": True})  # Not a list


if __name__ == "__main__":
    pytest.main([__file__])