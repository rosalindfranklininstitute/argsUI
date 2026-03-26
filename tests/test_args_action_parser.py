# SPDX-FileCopyrightText: 2026 Duncan McDougall <duncan.mcdougall@rfi.ac.uk>
#
# SPDX-License-Identifier: Apache-2.0

from dataclasses import dataclass, MISSING, fields
from pathlib import Path

import datargs as dargs

import pytest


def test_store_bool():

    @dataclass
    class BoolOptions:
        store_true: bool = dargs.arg_field(action="store_true")
        store_false: bool = dargs.arg_field(action="store_false")

    for field in fields(BoolOptions):
        action = dargs.parse_field(field)
        assert action is not None

        assert action.action == field.name
        assert action.default == MISSING
        assert len(action.aliases) == 1
        assert action.aliases[0].startswith("--store-")

        args_kw_args = action.to_argument_kwargs()
        assert "default" not in args_kw_args
        assert "type" not in args_kw_args


def test_nargs():
    @dataclass
    class ValidOptions:
        a: int = dargs.arg_field(nargs=1)
        b: list[int] = dargs.arg_field(nargs=2)
        c: list[int] = dargs.arg_field(nargs="+")
        d: list[int] = dargs.arg_field(nargs="*")
        e: int = dargs.arg_field(nargs="?")

    for field in fields(ValidOptions):
        action = dargs.parse_field(field)
        assert action is not None

        assert action.value_type is int

    @dataclass
    class InvalidOptions:
        a: int = dargs.arg_field(nargs=2)

    with pytest.raises(RuntimeError):
        for field in fields(InvalidOptions):
            dargs.parse_field(field)


def test_append():
    @dataclass
    class ValidOptions:
        store: int = dargs.arg_field(action="store")
        append: list[int] = dargs.arg_field(action="append")
        append_nargs: list[list[int]] = dargs.arg_field(action="append", nargs=2)

    for field in fields(ValidOptions):
        action = dargs.parse_field(field)
        assert action is not None

        assert action.value_type is int

    @dataclass
    class InvalidOptions:
        append: int = dargs.arg_field(action="append")
        append_nargs: list[int] = dargs.arg_field(action="append", nargs=2)

    for field in fields(InvalidOptions):
        with pytest.raises(RuntimeError):
            dargs.parse_field(field)


def test_types():
    @dataclass
    class ValidOptions:
        int_val: int = dargs.arg_field()
        float_val: float = dargs.arg_field()
        bool_val: bool = dargs.arg_field()
        str_val: str = dargs.arg_field()
        Path_val: Path = dargs.arg_field()

    types = dict(
        int_val=int, float_val=float, bool_val=bool, str_val=str, Path_val=Path
    )

    for field in fields(ValidOptions):
        action = dargs.parse_field(field)
        assert action is not None

        assert action.value_type == types[action.dest]
        assert action.aliases[0] == f"--{action.dest.replace('_', '-')}"
