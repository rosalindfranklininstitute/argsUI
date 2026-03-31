import argparse
from dataclasses import dataclass
from pathlib import Path

import datargs as dargs

import pytest

from icecream import ic


@pytest.fixture(scope="session")
def test_files(tmp_path_factory):
    fn = tmp_path_factory.mktemp("data") / "config.toml"
    fn.touch()

    return fn


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
