# SPDX-FileCopyrightText: 2026 Duncan McDougall <duncan.mcdougall@rfi.ac.uk>
#
# SPDX-License-Identifier: Apache-2.0

from typing import Any
import argparse
from dataclasses import dataclass
from pathlib import Path
import sys
import tomllib

from .args import arg_field, PartialParsedArgs, ActionList


@dataclass
class ConfigFileArgs:
    config: Path = arg_field(
        "-c",
        doc="The path to a configuration file. This config file can be used instead of passing files into the command line. It is a TOML formatted file. The arguments will be read out of the name of the program.",
        default=None,
        required=False,
    )

    @classmethod
    def parse_config(cls, prog: str, args=None) -> PartialParsedArgs:
        args = args if args is not None else sys.argv[1:]
        config_parser = argparse.ArgumentParser(
            "config_parser", add_help=False, allow_abbrev=False
        )
        config_parser.add_argument(
            "-c", "--config", dest="config", default=None, type=Path
        )
        config_args, remaining_args = config_parser.parse_known_args(args)
        config_dict: dict[str, Any] = dict()
        config_file_args = []
        if config_args.config is not None:
            with open(config_args.config, "rb") as fle:
                config_dict = tomllib.load(fle)
            if prog in config_dict:
                action_dict = ActionList.from_dataclass(cls).aliase_dict()
                for k, v in config_dict[prog].items():
                    if k in action_dict:
                        config_file_args.extend(action_dict[k].to_cli(v))
                    else:
                        raise ValueError(
                            f"Option '{k}' is not a valid long option for {prog}"
                        )
                del config_dict[prog]

        return PartialParsedArgs([*config_file_args, *remaining_args], config_dict)

    @classmethod
    def parse_args(
        cls, parser: argparse.ArgumentParser, args=None
    ) -> tuple[argparse.Namespace, dict[str, Any]]:

        partial_args = cls.parse_config(parser.prog, args)

        return parser.parse_args(partial_args.remaining_args), partial_args.config
