# SPDX-FileCopyrightText: 2026 Duncan McDougall <duncan.mcdougall@rfi.ac.uk>
#
# SPDX-License-Identifier: Apache-2.0

import argparse
from dataclasses import dataclass
from pathlib import Path

import pytest

import argsui as dargs


@dataclass
class BasicOptions:
    file: Path = dargs.arg_field(
        type=dargs.FilePathType(must_exist=False), default=None
    )
    number: int = dargs.arg_field(default=12)
    store_true: bool = dargs.arg_field(action="store_true")
    store_false: bool = dargs.arg_field(action="store_false")
    string: str = dargs.arg_field(default=None)
    const: str = dargs.arg_field(const="used", default="unused", action="store_const")
    lst: list[int] = dargs.arg_field(default=None, nargs=2)
    not_an_arg: int = dargs.no_arg_field(default=0)


@dataclass
class OuterOptions:
    name: str = dargs.arg_field(default=None)
    nested: BasicOptions = dargs.arg_field(default_factory=BasicOptions)


@pytest.fixture
def output_file(tmp_path_factory):
    fn = tmp_path_factory.mktemp("data") / "output.txt"
    return fn


def test_default_outer():
    parser = argparse.ArgumentParser(prog="test")
    dargs.add_arguments(parser, OuterOptions)
    args = parser.parse_args(args=[])

    options = dargs.from_arguments(args, OuterOptions)

    assert options.name is None
    assert options.nested.file is None
    assert options.nested.number == 12
    assert options.nested.store_true is False
    assert options.nested.store_false is True
    assert options.nested.string is None
    assert options.nested.const == "unused"
    assert options.nested.lst is None
    assert options.nested.not_an_arg == 0


def test_filled_outer(output_file):
    parser = argparse.ArgumentParser(prog="test")
    dargs.add_arguments(parser, OuterOptions)

    parser.print_help()
    args = parser.parse_args(
        args=[
            "--name",
            "name",
            "--nested.file",
            str(output_file),
            "--nested.number",
            str(15),
            "--nested.store-true",
            "--nested.store-false",
            "--nested.string",
            "string",
            "--nested.const",
            "--nested.lst",
            str(1),
            str(2),
        ]
    )
    options = dargs.from_arguments(args, OuterOptions)

    assert options.name == "name"
    assert options.nested.file == output_file
    assert options.nested.number == 15
    assert options.nested.store_true is True
    assert options.nested.store_false is False
    assert options.nested.string == "string"
    assert options.nested.const == "used"
    assert options.nested.lst == [1, 2]
    assert options.nested.not_an_arg == 0


def test_not_an_arg():
    parser = argparse.ArgumentParser(prog="test")
    dargs.add_arguments(parser, OuterOptions)

    with pytest.raises(SystemExit):
        parser.parse_args(args=["--not-an-arg"])


def test_nargs_outer(output_file):
    parser = argparse.ArgumentParser(prog="test")

    @dataclass
    class ValidNargsOuterInt:
        nested: BasicOptions = dargs.arg_field(default_factory=BasicOptions, nargs=1)

    parser = argparse.ArgumentParser(prog="test")
    dargs.add_arguments(parser, ValidNargsOuterInt)

    @dataclass
    class InvalidNargsOuterInt:
        nested: list[BasicOptions] = dargs.arg_field(default_factory=list, nargs=2)

    parser = argparse.ArgumentParser(prog="test")
    with pytest.raises(TypeError, match=".*nargs.*"):
        dargs.add_arguments(parser, InvalidNargsOuterInt)

    @dataclass
    class MultiNargsOuterStr:
        nested: list[BasicOptions] = dargs.arg_field(default_factory=list, nargs="+")

    parser = argparse.ArgumentParser(prog="test")
    with pytest.raises(TypeError, match=".*nargs.*"):
        dargs.add_arguments(parser, MultiNargsOuterStr)

    @dataclass
    class OptionalNargsOuterStr:
        nested: BasicOptions = dargs.arg_field(default_factory=BasicOptions, nargs="?")

    parser = argparse.ArgumentParser(prog="test")
    with pytest.raises(TypeError, match=".*nargs.*"):
        dargs.add_arguments(parser, OptionalNargsOuterStr)


def test_invalid_nargs_inner(output_file):

    @dataclass
    class FixedNargsInner:
        lst: list[int] = dargs.arg_field(default=None, nargs=2)

    @dataclass
    class FixedOuter:
        nested: FixedNargsInner = dargs.arg_field(default_factory=FixedNargsInner)

    parser = argparse.ArgumentParser(prog="test")
    dargs.add_arguments(parser, FixedOuter)

    @dataclass
    class VarNargsInner:
        lst: list[int] = dargs.arg_field(default=None, nargs="+")

    @dataclass
    class VarOuter:
        nested: VarNargsInner = dargs.arg_field(default_factory=VarNargsInner)

    parser = argparse.ArgumentParser(prog="test")
    with pytest.raises(TypeError, match=".*nargs.*"):
        dargs.add_arguments(parser, VarOuter)


def test_nested(output_file):

    @dataclass
    class Inner:
        name: str = dargs.arg_field(default=None)
        inner: BasicOptions = dargs.arg_field(default_factory=BasicOptions)

    @dataclass
    class Outer:
        name: str = dargs.arg_field(default=None)
        nested: Inner = dargs.arg_field(default_factory=Inner)

    parser = argparse.ArgumentParser(prog="test")
    dargs.add_arguments(parser, Outer)

    parser.print_help()
    args = parser.parse_args(
        args=[
            "--name",
            "name",
            "--nested.name",
            "inner",
            "--nested.inner.file",
            str(output_file),
            "--nested.inner.number",
            str(15),
            "--nested.inner.store-true",
            "--nested.inner.store-false",
            "--nested.inner.string",
            "string",
            "--nested.inner.const",
            "--nested.inner.lst",
            str(1),
            str(2),
        ]
    )
    options = dargs.from_arguments(args, Outer)

    assert options.name == "name"
    assert options.nested.name == "inner"
    assert options.nested.inner.file == output_file
    assert options.nested.inner.number == 15
    assert options.nested.inner.store_true is True
    assert options.nested.inner.store_false is False
    assert options.nested.inner.string == "string"
    assert options.nested.inner.const == "used"
    assert options.nested.inner.lst == [1, 2]
    assert options.nested.inner.not_an_arg == 0


def test_list_outer(output_file):
    @dataclass
    class ListOuterBasic:
        name: str = dargs.arg_field(default=None)
        nested: list[BasicOptions] = dargs.arg_field(
            default_factory=list, action="append"
        )

    parser = argparse.ArgumentParser(prog="test")
    dargs.add_arguments(parser, ListOuterBasic)

    parser.print_help()
    args = parser.parse_args(
        args=[
            "--name",
            "name",
            "--nested.file",
            str(output_file),
            "--nested.number",
            str(15),
            "--nested.number",
            str(16),
            "--nested.store-true",
            "--nested.store-false",
            "--nested.string",
            "string",
            "--nested.const",
            "--nested.lst",
            str(1),
            str(2),
            "--nested.lst",
            str(2),
            str(3),
        ]
    )
    options = dargs.from_arguments(args, ListOuterBasic)

    assert options.name == "name"

    assert options.nested[0].file == output_file
    assert options.nested[0].number == 15
    assert options.nested[0].store_true is True
    assert options.nested[0].store_false is False
    assert options.nested[0].string == "string"
    assert options.nested[0].const == "used"
    assert options.nested[0].lst == [1, 2]
    assert options.nested[0].not_an_arg == 0

    assert options.nested[1].file is None
    assert options.nested[1].number == 16
    assert options.nested[1].store_true is False
    assert options.nested[1].store_false is True
    assert options.nested[1].string is None
    assert options.nested[1].const == "unused"
    assert options.nested[1].lst == [2, 3]
    assert options.nested[1].not_an_arg == 0


def test_list_inner(output_file):
    @dataclass
    class ListOptions:
        name: str = dargs.arg_field(default=None)
        lst: list[int] = dargs.arg_field(action="append", default_factory=list)

    @dataclass
    class Outer:
        name: str = dargs.arg_field(default=None)
        nested: ListOptions = dargs.arg_field(default_factory=ListOptions)

    parser = argparse.ArgumentParser(prog="test")
    dargs.add_arguments(parser, Outer)

    parser.print_help()
    args = parser.parse_args(
        args=[
            "--name",
            "name",
            "--nested.name",
            "inner",
            "--nested.lst",
            str(15),
            "--nested.lst",
            str(16),
        ]
    )
    options = dargs.from_arguments(args, Outer)

    assert options.name == "name"

    assert options.nested.name == "inner"
    assert options.nested.lst == [15, 16]


def test_list_list(output_file):
    @dataclass
    class ListOptions:
        name: str = dargs.arg_field()
        lst: list[int] = dargs.arg_field(action="append")

    @dataclass
    class ListOuter:
        name: str = dargs.arg_field(default=None)
        nested: list[ListOptions] = dargs.arg_field(
            default_factory=list, action="append"
        )

    parser = argparse.ArgumentParser(prog="test")
    with pytest.raises(NotImplementedError, match="append on nested.*"):
        dargs.add_arguments(parser, ListOuter)


def test_nested_list_outer(output_file):

    @dataclass
    class Inner:
        name: str = dargs.arg_field(default="dogs")

    @dataclass
    class Middle:
        name: str = dargs.arg_field(default="cats")
        inner: Inner = dargs.arg_field(default_factory=Inner)

    @dataclass
    class Outer:
        name: str = dargs.arg_field(default=None)
        middle: list[Middle] = dargs.arg_field(default_factory=list, action="append")

    parser = argparse.ArgumentParser(prog="test")
    dargs.add_arguments(parser, Outer)

    parser.print_help()
    args = parser.parse_args(
        args=[
            "--name",
            "name",
            "--middle.name",
            "middle1",
            "--middle.inner.name",
            "inner1",
            "--middle.inner.name",
            "inner2",
        ]
    )
    options = dargs.from_arguments(args, Outer)

    assert options.name == "name"
    assert len(options.middle) == 2
    assert options.middle[0].name == "middle1"
    assert options.middle[0].inner.name == "inner1"

    assert options.middle[1].name == "cats"
    assert options.middle[1].inner.name == "inner2"


def test_nested_list_middle(output_file):

    @dataclass
    class Inner:
        name: str = dargs.arg_field(default="dogs")

    @dataclass
    class Middle:
        name: str = dargs.arg_field(default="cats")
        inner: list[Inner] = dargs.arg_field(default_factory=Inner, action="append")

    @dataclass
    class Outer:
        name: str = dargs.arg_field(default=None)
        middle: Middle = dargs.arg_field(default_factory=Middle)

    parser = argparse.ArgumentParser(prog="test")
    dargs.add_arguments(parser, Outer)

    parser.print_help()
    args = parser.parse_args(
        args=[
            "--name",
            "name",
            "--middle.name",
            "middle1",
            "--middle.inner.name",
            "inner1",
            "--middle.inner.name",
            "inner2",
        ]
    )
    options = dargs.from_arguments(args, Outer)

    assert options.name == "name"
    assert options.middle.name == "middle1"
    assert len(options.middle.inner) == 2
    assert options.middle.inner[0].name == "inner1"
    assert options.middle.inner[1].name == "inner2"
