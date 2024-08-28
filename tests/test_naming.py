import pytest
from hypster import HP, config

def test_variable_naming():
    @config
    def config_func(hp: HP):
        var1 = hp.select(['a', 'b'], default='a')
        var2 = hp.number_input(10)

    # Test with defaults
    result = config_func()
    assert result['var1'] == 'a'
    assert result['var2'] == 10

    # Test with selections
    result = config_func(selections={'var1': 'b'})
    assert result['var1'] == 'b'
    assert result['var2'] == 10

    # Test with overrides
    result = config_func(overrides={'var2': 20})
    assert result['var1'] == 'a'
    assert result['var2'] == 20

def test_dict_naming():
    @config
    def config_func(hp: HP):
        config = {
            'model_type': hp.select(['cnn', 'rnn'], default='cnn'),
            'learning_rate': hp.number_input(0.001)
        }

    # Test with defaults
    result = config_func()
    assert result['config']['model_type'] == 'cnn'
    assert result['config']['learning_rate'] == 0.001

    # Test with selections
    result = config_func(selections={'config.model_type': 'rnn'})
    assert result['config']['model_type'] == 'rnn'
    assert result['config']['learning_rate'] == 0.001

    # Test with overrides
    result = config_func(overrides={'config.learning_rate': 0.01})
    assert result['config']['model_type'] == 'cnn'
    assert result['config']['learning_rate'] == 0.01

def test_nested_naming():
    @config
    def config_func(hp: HP):
        outer = {
            'inner': {
                'deep': hp.select(['x', 'y'], default='x'),
                'value': hp.number_input(5)
            }
        }

    # Test with defaults
    result = config_func()
    assert result['outer']['inner']['deep'] == 'x'
    assert result['outer']['inner']['value'] == 5

    # Test with selections
    result = config_func(selections={'outer.inner.deep': 'y'})
    assert result['outer']['inner']['deep'] == 'y'
    assert result['outer']['inner']['value'] == 5

    # Test with overrides
    result = config_func(overrides={'outer.inner.value': 10})
    assert result['outer']['inner']['deep'] == 'x'
    assert result['outer']['inner']['value'] == 10

def test_class_naming():
    @config
    def config_func(hp: HP):
        class ModelConfig:
            def __init__(self, model_type, learning_rate):
                self.model_type = model_type
                self.learning_rate = learning_rate

        model = ModelConfig(
            model_type=hp.select(['cnn', 'rnn'], default='cnn'),
            learning_rate=hp.number_input(0.001)
        )

    # Test with defaults
    result = config_func()
    assert result['model'].model_type == 'cnn'
    assert result['model'].learning_rate == 0.001

    # Test with selections
    result = config_func(selections={'model.model_type': 'rnn'})
    assert result['model'].model_type == 'rnn'
    assert result['model'].learning_rate == 0.001

    # Test with overrides
    result = config_func(overrides={'model.learning_rate': 0.01})
    assert result['model'].model_type == 'cnn'
    assert result['model'].learning_rate == 0.01

def test_function_naming():
    @config
    def config_func(hp: HP):
        def inner_func(param1, param2):
            return param1, param2

        result = inner_func(
            param1=hp.select(['a', 'b'], default='a'),
            param2=hp.number_input(10)
        )

    # Test with defaults
    result = config_func()
    assert result['result'][0] == 'a'
    assert result['result'][1] == 10

    # Test with selections
    result = config_func(selections={'result.param1': 'b'})
    assert result['result'][0] == 'b'
    assert result['result'][1] == 10

    # Test with overrides
    result = config_func(overrides={'result.param2': 20})
    assert result['result'][0] == 'a'
    assert result['result'][1] == 20

# Add more tests as needed