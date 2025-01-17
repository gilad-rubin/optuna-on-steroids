# Boolean Types

Hypster provides boolean parameter configuration through `bool` and `multi_bool` methods. These methods handle boolean values without additional validation.

## Function Signatures

```python
def bool(
    default: bool,
    *,
    name: Optional[str] = None
) -> bool

def multi_bool(
    default: List[bool] = [],
    *,
    name: Optional[str] = None
) -> List[bool]
```

## Usage Examples

### Single Boolean Values

```python
# Single boolean parameter with default
stream = hp.bool(True)
use_cache = hp.bool(False)

# Usage
config(values={"stream": False})
config(values={"use_cache": True})
```

### Multiple Boolean Values

```python
# Multiple boolean parameters with defaults
layer_trainable = hp.multi_bool([True, True, False])
feature_flags = hp.multi_bool([False, False])

# Usage
config(values={"layer_trainable": [False, True, True]})
config(values={"feature_flags": [True, False, True]})
```

### Invalid Values

```python
# These will raise errors
config(values={"stream": "true"})  # String instead of boolean
config(values={"layer_trainable": [1, 0]})  # Numbers instead of booleans
```

## Reproducibility

All boolean parameters are fully serializable and reproducible:

```python
# Configuration will be exactly reproduced
snapshot = config.get_last_snapshot()
restored_config = config(values=snapshot)
```
