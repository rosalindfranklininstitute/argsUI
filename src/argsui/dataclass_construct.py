# SPDX-FileCopyrightText: 2026 Duncan McDougall <duncan.mcdougall@rfi.ac.uk>
#
# SPDX-License-Identifier: Apache-2.0
#
# Produced based on output of:GPT-5.4 Nano:
# """
# Given a dictionary that represents the properties of a python dataclass,
# where the dataclass may have other dataclasses as fields,
# use the dictionary to constructt the dataclass.
# """
from dataclasses import is_dataclass, fields
from typing import Any, get_args, get_origin, get_type_hints, Optional, Union


def _is_optional(t):
    origin = get_origin(t)
    if origin is Union:
        args = get_args(t)
        return len(args) == 2 and type(None) in args
    return False


def _strip_optional(t):
    if _is_optional(t):
        return next(a for a in get_args(t) if a is not type(None))
    return t


def _build_value(expected_type, value):
    if value is None:
        return None

    expected_type = _strip_optional(expected_type)

    if isinstance(expected_type, type) and is_dataclass(expected_type):
        if not isinstance(value, dict):
            raise TypeError(
                f"Expected dict for {expected_type}, got {type(value).__name__}"
            )
        return build_dataclass_from_dict(expected_type, value)

    origin = get_origin(expected_type)
    if origin in (list, tuple, set):
        (item_type,) = get_args(expected_type) or (Any,)
        if not isinstance(value, (list, tuple, set)):
            raise TypeError(
                f"Expected {origin.__name__} for {expected_type}, got {type(value).__name__}"
            )
        built_items = [_build_value(item_type, v) for v in value]
        return origin(built_items)

    if origin is dict:
        key_type, val_type = (
            get_args(expected_type) if get_args(expected_type) else (Any, Any)
        )
        if not isinstance(value, dict):
            raise TypeError(
                f"Expected dict for {expected_type}, got {type(value).__name__}"
            )
        return {
            _build_value(key_type, k): _build_value(val_type, v)
            for k, v in value.items()
        }

    return value


def build_dataclass_from_dict(dataclass_type, data: dict):
    if not (isinstance(dataclass_type, type) and is_dataclass(dataclass_type)):
        raise TypeError(f"{dataclass_type} must be a dataclass type")

    if not isinstance(data, dict):
        raise TypeError(f"data must be a dict, got {type(data).__name__}")

    type_hints = get_type_hints(dataclass_type)

    kwargs = {}
    for f in fields(dataclass_type):
        name = f.name
        if name not in data:
            continue

        expected_type = type_hints.get(name, Any)
        kwargs[name] = _build_value(expected_type, data[name])

    return dataclass_type(**kwargs)
