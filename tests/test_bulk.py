# SPDX-FileCopyrightText: 2026 Duncan McDougall <duncan.mcdougall@rfi.ac.uk>
#
# SPDX-License-Identifier: Apache-2.0

from typing import Any
from dataclasses import dataclass
from pathlib import Path
import argparse
import os

import datargs as dargs

import pytest

from icecream import install

install()


@dataclass
class BasicOptions(dargs.ConfigFileArgs):
    in_file: Path = dargs.arg_field(
        type=dargs.FilePathType(must_exist=False), required=True, default=None
    )
    out_file: Path = dargs.arg_field(
        type=dargs.FilePathType(must_exist=False), required=True, default=None
    )
    number: int = dargs.arg_field(default=12)
    append: list[int] = dargs.arg_field(action="append", default_factory=list)
    nargs: list[int] = dargs.arg_field(nargs=2, default_factory=list)
    append_nargs: list[list[int]] = dargs.arg_field(
        action="append", nargs=2, default_factory=list
    )


def process(args: BasicOptions, config: dict[str, Any]) -> None:
    with open(args.in_file, "r") as in_fle:
        num = int(in_fle.readline().strip())
        with open(args.out_file, "w") as out_fle:
            out_fle.write(str(num + args.number) + "\n")


class NumberFile(dargs.FileDetails):
    def file_extension(self) -> str:
        return ".txt"

    def filter(self, path: Path) -> bool:
        return True

    def target_name(self, in_path: Path) -> Path:
        return in_path.with_suffix(".num")


@pytest.fixture(scope="function")
def output_file(tmp_path_factory) -> tuple[Path, Path]:
    in_dir = tmp_path_factory.mktemp("in")
    for ii in range(5):
        tmp = Path(in_dir / f"{ii + 1}/")
        tmp.mkdir()
        with open(tmp / f"test_{ii + 1}.txt", "w") as fle:
            fle.write(str(ii) + "\n")
    out_dir = tmp_path_factory.mktemp("out")
    return in_dir, out_dir


@pytest.fixture(scope="session")
def config_file(tmp_path_factory):
    fn = tmp_path_factory.mktemp("data") / "config.toml"
    with open(fn, "w") as fle:
        fle.write("""
        [bulk_basic]
        number=36
        append=[1,2,3]
        nargs=[1,2]
        append-nargs=[[1,2],[2,3]]
        """)

    return fn


@pytest.fixture(scope="function")
def individual_config_files(output_file):
    in_dir = output_file[0]
    for ii in range(5):
        tmp = Path(in_dir / f"{ii + 1}/")
        assert tmp.exists()
        with open(tmp / "config.toml", "w") as fle:
            fle.write(f"""
            [basic]
            number={ii}
            nargs=[1,{ii}]
            """)
    return None


def test_basic(output_file):

    assert len(os.listdir(output_file[0])) == 5
    assert len(os.listdir(output_file[1])) == 0

    dargs.process_bulk(
        "basic",
        BasicOptions,
        process,
        NumberFile(),
        input_arg_name="in_file",
        output_arg_name="out_file",
        args=[
            "--dir",
            output_file[0].as_posix(),
            "--output",
            output_file[1].as_posix(),
            "--number",
            "24",
            "--nargs",
            "12",
            "13",
            "--append",
            "21",
            "--append",
            "22",
            "--append-nargs",
            "31",
            "32",
            "--append-nargs",
            "41",
            "42",
        ],
    )
    assert len(os.listdir(output_file[1])) == 5

    for ii in range(5):
        path: Path = output_file[1] / str(ii + 1) / f"test_{ii + 1}.num"
        assert path.exists()
        assert int(path.read_text()) == ii + 24


def test_defaults(output_file):

    assert len(os.listdir(output_file[0])) == 5
    assert len(os.listdir(output_file[1])) == 0

    dargs.process_bulk(
        "basic",
        BasicOptions,
        process,
        NumberFile(),
        input_arg_name="in_file",
        output_arg_name="out_file",
        args=[
            "--dir",
            output_file[0].as_posix(),
            "--output",
            output_file[1].as_posix(),
        ],
    )
    assert len(os.listdir(output_file[1])) == 5

    for ii in range(5):
        path: Path = output_file[1] / str(ii + 1) / f"test_{ii + 1}.num"
        assert path.exists()
        assert int(path.read_text()) == ii + 12


def test_dest_aliase_mismatch(output_file):
    @dataclass
    class MissmatchOptions(dargs.ConfigFileArgs):
        in_file: Path = dargs.arg_field(
            "--input",
            arg_type=dargs.ArgType.EXPLICIT_ONLY,
            type=dargs.FilePathType(must_exist=False),
            required=True,
            default=None,
        )
        out_file: Path = dargs.arg_field(
            "--output",
            arg_type=dargs.ArgType.EXPLICIT_ONLY,
            type=dargs.FilePathType(must_exist=False),
            required=True,
            default=None,
        )
        number: int = dargs.arg_field(default=12)
        append: list[int] = dargs.arg_field(action="append", default_factory=list)
        nargs: list[int] = dargs.arg_field(nargs=2, default_factory=list)
        append_nargs: list[list[int]] = dargs.arg_field(
            action="append", nargs=2, default_factory=list
        )

    assert len(os.listdir(output_file[0])) == 5
    assert len(os.listdir(output_file[1])) == 0

    dargs.process_bulk(
        "basic",
        MissmatchOptions,
        process,
        NumberFile(),
        input_arg_name="in_file",
        output_arg_name="out_file",
        args=[
            "--dir",
            output_file[0].as_posix(),
            "--output",
            output_file[1].as_posix(),
        ],
    )
    assert len(os.listdir(output_file[1])) == 5

    for ii in range(5):
        path: Path = output_file[1] / str(ii + 1) / f"test_{ii + 1}.num"
        assert path.exists()
        assert int(path.read_text()) == ii + 12


def test_config(output_file, config_file):

    assert len(os.listdir(output_file[0])) == 5
    assert len(os.listdir(output_file[1])) == 0

    dargs.process_bulk(
        "basic",
        BasicOptions,
        process,
        NumberFile(),
        input_arg_name="in_file",
        output_arg_name="out_file",
        args=[
            "--dir",
            output_file[0].as_posix(),
            "--output",
            output_file[1].as_posix(),
            "--config",
            str(config_file),
        ],
    )
    assert len(os.listdir(output_file[1])) == 5

    for ii in range(5):
        path: Path = output_file[1] / str(ii + 1) / f"test_{ii + 1}.num"
        assert path.exists()
        assert int(path.read_text()) == ii + 36


def test_each_config(output_file, individual_config_files):

    assert len(os.listdir(output_file[0])) == 5
    assert len(os.listdir(output_file[1])) == 0

    dargs.process_bulk(
        "basic",
        BasicOptions,
        process,
        NumberFile(),
        input_arg_name="in_file",
        output_arg_name="out_file",
        args=[
            "--dir",
            output_file[0].as_posix(),
            "--output",
            output_file[1].as_posix(),
        ],
    )
    assert len(os.listdir(output_file[1])) == 5

    for ii in range(5):
        path: Path = output_file[1] / str(ii + 1) / f"test_{ii + 1}.num"
        assert path.exists()
        assert int(path.read_text()) == ii + ii
