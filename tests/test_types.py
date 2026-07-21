from enum import Enum
import argparse
from dataclasses import dataclass, fields
from pathlib import Path

import datargs as dargs

import pytest


@pytest.fixture(scope="session")
def test_files(tmp_path_factory):
    fn = tmp_path_factory.mktemp("data") / "config.toml"
    fn.touch()

    return fn


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
        action = dargs.from_field(field)
        assert action is not None

        assert action.value_type == types[action.dest]
        assert action.aliases[0] == f"--{action.dest.replace('_', '-')}"


def test_enums():
    class EnumValue(Enum):
        FIRST = 1
        SECOND = 2
        THIRD = 2

    @dataclass
    class ValidOptions:
        complete: EnumValue = dargs.arg_field(action="store")
        partial: EnumValue = dargs.arg_field(
            action="store", choices=[EnumValue.FIRST, EnumValue.THIRD]
        )

    for field in fields(ValidOptions):
        action = dargs.from_field(field)
        assert action is not None
        assert action.value_type is EnumValue
        assert action.choices is not None
        if action.dest == "complete":
            assert action.choices == [t for t in EnumValue]
        else:
            assert len(action.choices) == 2

    @dataclass
    class InvalidOptions:
        store: EnumValue = dargs.arg_field(action="store", default=17)
        store: EnumValue = dargs.arg_field(
            action="store", choices=[EnumValue.FIRST, 17]
        )

    for field in fields(InvalidOptions):
        with pytest.raises(TypeError):
            dargs.from_field(field)


def test_file_may_not_exist(test_files):

    @dataclass
    class Options:
        fle: Path = dargs.arg_field(
            arg_type=dargs.ArgType.POSITIONAL, type=dargs.FilePathType(False)
        )

    parser = argparse.ArgumentParser(prog="test")

    dargs.add_arguments(parser, Options)

    args = parser.parse_args([str(test_files)])
    assert args.fle.is_file()

    args = parser.parse_args(["non existant file.txt"])
    assert not args.fle.is_file()

    with pytest.raises(SystemExit):
        parser.parse_args([str(test_files.parent)])


def test_file_must_exist(test_files):

    @dataclass
    class Options:
        fle: Path = dargs.arg_field(
            arg_type=dargs.ArgType.POSITIONAL, type=dargs.FilePathType(True)
        )

    parser = argparse.ArgumentParser(prog="test")

    dargs.add_arguments(parser, Options)

    args = parser.parse_args([str(test_files)])
    assert args.fle.is_file()

    with pytest.raises(SystemExit):
        parser.parse_args(["non existant file.txt"])

    with pytest.raises(SystemExit):
        parser.parse_args([str(test_files.parent)])


def test_dir_may_not_exist(test_files):

    @dataclass
    class Options:
        fle: Path = dargs.arg_field(
            arg_type=dargs.ArgType.POSITIONAL, type=dargs.DirPathType(False)
        )

    parser = argparse.ArgumentParser(prog="test")

    dargs.add_arguments(parser, Options)

    args = parser.parse_args([str(test_files.parent)])
    assert args.fle.is_dir()

    args = parser.parse_args(["non existant dir"])
    assert not args.fle.is_dir()

    with pytest.raises(SystemExit):
        parser.parse_args([str(test_files)])


def test_dir_must_exist(test_files):

    @dataclass
    class Options:
        fle: Path = dargs.arg_field(
            arg_type=dargs.ArgType.POSITIONAL, type=dargs.DirPathType(True)
        )

    parser = argparse.ArgumentParser(prog="test")

    dargs.add_arguments(parser, Options)

    args = parser.parse_args([str(test_files.parent)])
    assert args.fle.is_dir()

    with pytest.raises(SystemExit):
        parser.parse_args(["non existant dir"])

    with pytest.raises(SystemExit):
        parser.parse_args([str(test_files)])


def test_types_must_match(test_files):

    @dataclass
    class PathOptions:
        fle: Path = dargs.arg_field(
            arg_type=dargs.ArgType.POSITIONAL, type=dargs.DirPathType(True)
        )

    @dataclass
    class IntOptions:
        fle: int = dargs.arg_field(
            arg_type=dargs.ArgType.POSITIONAL, type=dargs.DirPathType(True)
        )

    parser = argparse.ArgumentParser(prog="test")

    dargs.add_arguments(parser, PathOptions)

    with pytest.raises(TypeError):
        dargs.add_arguments(parser, IntOptions)
