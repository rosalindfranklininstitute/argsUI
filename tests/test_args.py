# SPDX-FileCopyrightText: 2026 Duncan McDougall <duncan.mcdougall@rfi.ac.uk>
#
# SPDX-License-Identifier: Apache-2.0

from typing import Any
from dataclasses import dataclass
from pathlib import Path
import argparse

import datargs as dargs

import pytest


@dataclass
class BasicOptions:
    file: Path = dargs.arg_field(
        type=dargs.FilePathType(must_exist=False), required=True
    )
    number: int = dargs.arg_field(default=12)
    store_true: bool = dargs.arg_field(action="store_true")
    store_false: bool = dargs.arg_field(action="store_false")
    string: str = dargs.arg_field(default=None)
    lst: list[int] = dargs.arg_field(action="append", default_factory=list)


def process(args: BasicOptions, config: dict[str, Any]):
    with open(args.file, "w") as fle:
        fle.write(str(args.number) + "\n")
        fle.write(str(args.store_true) + "\n")
        fle.write(str(args.store_false) + "\n")
        fle.write(str(args.string) + "\n")
        fle.write(",".join([str(ii) for ii in args.lst]) + "\n")


@pytest.fixture(scope="function")
def output_file(tmp_path_factory):
    fn = tmp_path_factory.mktemp("data") / "output.txt"
    return fn


def test_bascic(output_file):
    parser = argparse.ArgumentParser(prog="test")
    dargs.add_arguments(parser, BasicOptions)

    args = parser.parse_args(
        args=[
            "--file",
            str(output_file),
            "--number",
            str(15),
            "--store-true",
            "--store-false",
            "--string",
            "string",
            "--lst",
            "1",
            "--lst",
            "2",
        ]
    )

    options = BasicOptions(**vars(args))
    process(options, dict())

    with open(output_file, "r") as fle:
        lines = [line.strip() for line in fle]
        assert lines[0] == str(options.number)
        assert lines[1] == str(options.store_true)
        assert lines[2] == str(options.store_false)
        assert lines[3] == str(options.string)
        assert lines[4] == "1,2"


def test_defaults(output_file):
    parser = argparse.ArgumentParser(prog="test")
    dargs.add_arguments(parser, BasicOptions)

    args = parser.parse_args(
        args=[
            "--file",
            str(output_file),
        ]
    )

    options = BasicOptions(**vars(args))
    process(options, dict())

    with open(output_file, "r") as fle:
        lines = [line.strip() for line in fle]
        assert lines[0] == str(12)
        assert lines[1] == str(False)
        assert lines[2] == str(True)
        assert lines[3] == str(None)
        assert lines[4] == ""
