from .const import BuilderReservedParams as r_params

from .types import (
    check_collection,
    check_is_callable,
    first,
    _flat
)

@_flat
def get_query_params(key, _qparams, fn_map=None, skip_value=None, defalut=None, prefer=None):
    if prefer is None:
        value = _qparams.get(key, defalut)
        if value is None:
            return {}
        value = fn_map(value) if fn_map and not (type(value) is fn_map) else value

        if skip_value is None:
            return {key: value}

        if check_collection(skip_value):
            if any(
                    len(get_query_params(key, _qparams, fn_map, skip_condition, defalut)) == 0  # condition
                    for skip_condition in skip_value  # collection
            ):
                return {}
        elif check_is_callable(skip_value) and skip_value(value):
            return {}
        elif value == skip_value:
            return {}

        return {key: value}
    return {
        key: prefer
    }
