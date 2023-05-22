import re
from enum import Enum
from functools import reduce
from typing import Dict, List

import six
from numpy import int8, int16, int32, int64
from sqlalchemy.exc import NoResultFound


def check_types(value, *int_types: type):
    return isinstance(value, int_types)


def check_complex(value):
    types_to_check = [
        check_collection,
        lambda _value: check_types(_value, dict)
    ]
    return any(
        map(
            lambda checker: checker(value),
            types_to_check
        )
    )


NUMBER_TYPES = [int8, int16, int32, int64, int, float]


def check_numbers(value):
    return check_types(value, *NUMBER_TYPES)


def check_boolean(value):
    return check_types(value, bool)


def check_basics_not_str(value):
    return check_numbers(value) or check_boolean(value)


def check_is_callable(value):
    return callable(value)


def check_collection(value):
    """check [tuple, list]"""
    return check_types(value, *[list, tuple])


def symbol(value, default, **kwargs):
    if len(kwargs) == 0:
        return default
    for k, v in kwargs.items():
        if check_types(v, type) and check_types(value, v):
            return k
        if check_collection(v):
            for _type in v:
                return symbol(value, default, **{k: _type})
        if v is None and value is None:
            return k
    return default


def get_first_if_collection_of_one(rl, map_func=None):
    r = first(rl) if check_collection(rl) and len(rl) == 1 else rl
    if map_func is None:
        return r
    if check_collection(r):
        return [map_func(i) for i in r]
    return map_func(r)


def append_all(*args):
    return reduce(
        lambda carr, curt: [*carr, *curt],
        args
    )


def first(col, raise_on_empty=True):
    try:
        return next(iter(col))
    except StopIteration as e:
        if raise_on_empty:
            raise NoResultFound('Empty collection')
        return None


def full(col, raise_on_empty=True):
    _result = list(iter(col))
    if len(_result) == 0 and raise_on_empty:
        raise NoResultFound('Empty collection')
    return _result


def _flat(function):
    def decorator(*args, flat=False, **kwargs):
        r: dict = function(*args, **kwargs)
        return first(r.values(), raise_on_empty=False) if flat else r

    return decorator


def _try(function):
    def decorator(args):
        try:
            return function(args)
        except Exception:
            return None

    return decorator


def list_to_dict(items: list[str], recursive=False):
    result = dict()
    for key in items:
        key_path = key.split('.')
        root_key: str = key_path.pop(0)
        _sub_object = result.get(root_key)
        v = key_path if len(key_path) > 0 else '*'
        if _sub_object is None:
            result[root_key] = v
        else:  # 😅 we fixit
            if isinstance(_sub_object, str):
                result[root_key] = []
            elif v == "*":
                continue
            result[root_key].append(*v)
    return {
        # key:
        key: (
            list_to_dict(value)
            if recursive and check_collection(value)
            else value
        )
        if len(value) > 1
        else value
        for key, value in result.items()
    }


def stack(row, key, new_name=None):
    prefix = f'{key}.'
    sub_obj = {
        k[len(prefix):]: v for k, v in row.items() if k.startswith(prefix)
    }
    return {
        **{
            k: v for k, v in row.items() if not k.startswith(prefix)
        },
        **({f'{key}_id': row[key]} if new_name in row else {}),
        new_name: sub_obj
    }


def get_obj_name(col_name, col=None):
    if col is None:
        return col_name
    new_name = re.sub('_id$', '', col_name)
    return f'{new_name}_nested' if new_name == col_name else new_name


def pop_key(obj, key):
    sub_obj = dict()
    sub_name = f'{key}.'
    for key, values in obj.items():
        if key.startswith(sub_name):
            sub_obj[key[len(sub_name):]] = values
    for key in sub_obj.keys():
        obj.pop(sub_name + key)

    # assert len(sub_obj) > 0, "Fatal el objeto para insertar"
    return sub_obj


aggfunction = re.compile('^agg__(?P<fieldName>.+)$')


def create_agg_dict(base_dict, key: str, value):
    field_match = aggfunction.match(key)
    if field_match:
        field = field_match.groupdict().get(
            'fieldName', ''
        )
        agg_function = base_dict.get(field, [])
        agg_function += [value]
        base_dict[field] = value
    return base_dict


class HTTPMethod:
    GET = 'GET'
    POST = 'POST'
    PUT = 'PUT'
    DELETE = 'DELETE'

    @classmethod
    def all_as_dict(cls, value=None) -> dict:
        return {
            http_method: value
            for http_method in cls.all()
        }

    @classmethod
    def all(cls):
        return [
            cls.GET,
            cls.POST,
            cls.PUT,
            cls.DELETE
        ]


# Python 3.10 don't have strtobool anymore. So we move it here.
# TRUE_VALUES = {"y", "yes", "t", "true", "on", "1"}
# FALSE_VALUES = {"n", "no", "f", "false", "off", "0"}
TRUE_VALUES = {"y", "yes", "t", "true", "on"}
FALSE_VALUES = {"n", "no", "f", "false", "off"}


def strtobool(value, extend=True):
    value = value.lower()

    if value in TRUE_VALUES:
        return True
    elif value in FALSE_VALUES:
        return False
    if check_numbers(value):
        value = str(value)

    if extend and strvalue == "1":
        return True
    if extend and value == "0":
        return False

    raise ValueError("Invalid truth value: " + value)


def convert_to_valid_boolean(value):
    if check_boolean(value):
        return value
    if check_numbers(value):
        return bool(value)
    if isinstance(value, str):
        return strtobool(value)
    raise ValueError


def check_valid_bool(value):
    if check_boolean(value):
        return True
    if check_numbers(value):
        return False
    if isinstance(value, str):
        return strtobool(value)
    raise ValueError


def append_on_dict(base: dict, key, new_item, validator=None):
    if key in base:
        if validator is None and new_item not in base[key]:
            base[key].append(new_item)
        elif validator and not any(map(validator, base[key])):
            base[key].append(new_item)
    else:
        base[key] = [new_item]


def remove_on_dict(base: Dict[object, List], key, lab_item_find):
    if key in base:
        for item in base[key]:
            if lab_item_find(item):
                base[key].remove(item)


import datetime
from datetime import timezone
import decimal
import json  # noqa
import uuid


def is_aware(value):
    """
    Determines if a given datetime.datetime is aware.

    The concept is defined in Python's docs:
    http://docs.python.org/library/datetime.html#datetime.tzinfo

    Assuming value.tzinfo is either None or a proper datetime.tzinfo,
    value.utcoffset() implements the appropriate logic.
    """
    return value.utcoffset() is not None


class JSONEncoder(json.JSONEncoder):
    """
    JSONEncoder subclass that knows how to encode date/time/timedelta,
    decimal types, generators and other basic python objects.
    """

    def default(self, obj):
        # For Date Time string spec, see ECMA 262
        # https://ecma-international.org/ecma-262/5.1/#sec-15.9.1.15
        if isinstance(obj, datetime.datetime):
            representation = obj.isoformat()
            if representation.endswith('+00:00'):
                representation = representation[:-6] + 'Z'
            return representation
        elif isinstance(obj, datetime.date):
            return obj.isoformat()
        elif isinstance(obj, datetime.time):
            if timezone and is_aware(obj):
                raise ValueError("JSON can't represent timezone-aware times.")
            representation = obj.isoformat()
            return representation
        elif isinstance(obj, datetime.timedelta):
            return six.text_type(obj.total_seconds())
        elif isinstance(obj, decimal.Decimal):
            # Serializers will coerce decimals to strings by default.
            return float(obj)
        elif isinstance(obj, uuid.UUID):
            return six.text_type(obj)
        elif isinstance(obj, bytes):
            # Best-effort for binary blobs. See #4187.
            return obj.decode('utf-8')
        elif hasattr(obj, 'tolist'):
            # Numpy arrays and array scalars.
            return obj.tolist()

        elif hasattr(obj, '__getitem__'):
            try:
                return dict(obj)
            except Exception:
                pass
        elif hasattr(obj, '__iter__'):
            return tuple(item for item in obj)
        elif isinstance(obj, Enum):
            return obj.value
        return super(JSONEncoder, self).default(obj)


def fix_pattern(_like):
    pattern = f'%{_like}%'

    if _like.endswith("$"):
        pattern = pattern[:-2]
    if _like.startswith("^"):
        pattern = pattern[2:]
    return pattern
