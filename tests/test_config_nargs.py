# SPDX-FileCopyrightText: 2026 Duncan McDougall <duncan.mcdougall@rfi.ac.uk>
#
# SPDX-License-Identifier: Apache-2.0

import argparse
from dataclasses import dataclass

import pytest

import argsui as dargs


@dataclass
class TestNargs(dargs.ConfigFileArgs):
    a: list[int] = dargs.arg_field(
        doc="A test argument", nargs=2, required=True, default_factory=list
    )

    b: list[int] = dargs.arg_field(
        doc="A test argument", action="append", required=True, default_factory=list
    )

    c: list[list[int]] = dargs.arg_field(
        doc="A test argument", nargs=2, action="append", default_factory=list
    )

    __test__ = False


@pytest.fixture(scope="session")
def config_file(tmp_path_factory):
    fn = tmp_path_factory.mktemp("data") / "config.toml"
    with open(fn, "w") as fle:
        fle.write("""
        [test]
        a=[1,2]
        c=[[1,2], [2,3]]

        [other]
        z = 12
        """)

    return fn


def test_normal_args():
    parser = argparse.ArgumentParser(prog="test")

    dargs.add_arguments(parser, TestNargs)

    args, config_dict = TestNargs.parse_args(
        parser,
        [
            "--a",
            "1",
            "2",
            "--b",
            "2",
            "--b",
            "3",
            "--c",
            "3",
            "4",
        ],
    )
    assert args.a == [1, 2]
    assert args.b == [2, 3]
    assert args.c == [[3, 4]]


def test_missing_args():
    parser = argparse.ArgumentParser(prog="test")

    dargs.add_arguments(parser, TestNargs)

    with pytest.raises(SystemExit):
        args, config_dict = TestNargs.parse_args(parser, ["--b", "2"])


def test_missing_args_in_config(config_file):
    parser = argparse.ArgumentParser(prog="test")

    dargs.add_arguments(parser, TestNargs)

    args, config_dict = TestNargs.parse_args(
        parser, ["--config", str(config_file), "--b", "2"]
    )
    assert args.a == [1, 2]
    assert args.b == [2]
    assert args.c == [[1, 2], [2, 3]]


def test_missing_args_with_config(config_file):
    parser = argparse.ArgumentParser(prog="test")

    dargs.add_arguments(parser, TestNargs)

    with pytest.raises(SystemExit):
        args, config_dict = TestNargs.parse_args(parser, ["--config", str(config_file)])


def test_override_args_from_config(config_file):
    parser = argparse.ArgumentParser(prog="test")

    dargs.add_arguments(parser, TestNargs)

    args, config_dict = TestNargs.parse_args(
        parser,
        [
            "--config",
            str(config_file),
            "--a",
            "1",
            "2",
            "--b",
            "2",
            "--b",
            "3",
            "--c",
            "3",
            "4",
        ],
    )
    assert args.a == [1, 2]
    assert args.b == [2, 3]
    assert args.c == [[1, 2], [2, 3], [3, 4]]


def test_addition_from_config(config_file):
    parser = argparse.ArgumentParser(prog="test")

    dargs.add_arguments(parser, TestNargs)

    args, config_dict = TestNargs.parse_args(
        parser, ["--config", str(config_file), "--b", "2"]
    )
    assert config_dict == dict(other=dict(z=12))


def test_help(capsys):
    parser = argparse.ArgumentParser(prog="test")

    dargs.add_arguments(parser, TestNargs)

    with pytest.raises(SystemExit):
        args, config_dict = TestNargs.parse_args(parser, ["--help"])

    captured = capsys.readouterr()

    assert captured.out == parser.format_help()
