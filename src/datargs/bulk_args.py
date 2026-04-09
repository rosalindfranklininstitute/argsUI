from typing import Any, Callable
from dataclasses import dataclass, fields, make_dataclass
from abc import ABC, abstractmethod

from pathlib import Path
import argparse

import datargs as nxargs
from .args import arg_field, ArgType, parse_fields, add_arguments, Action
from .interactive_args import InteractiveArgs, InteractiveBase, NoInteractiveArgs
from .config_args import ConfigFileArgs
from .extra_types import DirPathType


from icecream import ic


ProcessFunc = Callable[[Any, dict[str, Any]], None]


class FileDetails(ABC):
    @abstractmethod
    def file_extension(self) -> str:
        """
        Retruns the file extension (or other regex) that will be used to glob for
        files of interest.
        """
        pass

    @abstractmethod
    def filter(self, path: Path) -> bool:
        """
        Should return:
        - True if the specified file is of interest,
        - False if the file should be ignored.
        """
        pass

    @abstractmethod
    def target_name(self, in_path: Path) -> Path:
        pass


@dataclass
class ProcessArgs(ConfigFileArgs):
    in_path: Path = arg_field(
        "-d",
        "--dir",
        "--directory",
        required=True,
        arg_type=ArgType.EXPLICIT_ONLY,
        doc="The input directory.",
        default=None,
        type=DirPathType(True),
    )

    out_path: Path = arg_field(
        "-o",
        "--output",
        required=True,
        arg_type=ArgType.EXPLICIT_ONLY,
        doc="The output directory.",
        default=None,
        type=DirPathType(True),
    )

    config_name: list[str] = arg_field(
        doc="The possible names of config files.", action="append", default_factory=list
    )


def process_bulk(
    prog: str,
    args_class,
    process_func: ProcessFunc,
    file_details: FileDetails,
    input_arg_name: str = "input",
    output_arg_name: str = "output",
    args: list[str] | None = None,
) -> None:

    # Create a parser to parse the bulk options above and all the options in args_class, excluding input_arg_name and output_arg_name
    flds = [(f.name, f.type, f) for f in fields(ProcessArgs)]
    names_to_ignore = [input_arg_name, output_arg_name, *[f[0] for f in flds]]

    flds.extend(
        [
            (f.name, f.type, f)
            for f in fields(args_class)
            if f.name not in names_to_ignore
        ]
    )

    bases: list[type] = [ProcessArgs]
    if not isinstance(args_class, InteractiveBase):
        bases.append(InteractiveArgs)

    bulk_cls = make_dataclass("BulkArgs", fields=flds, bases=tuple(bases))

    # Process all the bulk args
    bulk_prog = f"bulk_{prog}"
    partial_args = bulk_cls.parse_config(bulk_prog, args=args)  # type: ignore
    process_args = bulk_cls.parse_interactive(  # type: ignore
        bulk_prog,
        exclude=["config"],
        args=partial_args.remaining_args,
    )

    config_names: list[str] = process_args.config_name
    if len(config_names) == 0:
        config_names.append("config.toml")

    # Find all the files to process
    names = set()
    file_sets: list[tuple[Path, Path, Path | None]] = []
    for file_path in process_args.in_path.glob(f"**/*{file_details.file_extension()}"):
        if not file_details.filter(file_path):
            continue
        relative_path = file_path.relative_to(process_args.in_path).parent
        out_folder = process_args.out_path / relative_path
        if not out_folder.exists():
            out_folder.mkdir(parents=True)
        out_path = out_folder / file_details.target_name(out_folder / file_path.name)
        file_name = file_path.name
        if file_name not in names:
            names.add(file_name)
        else:
            raise RuntimeError(f"Found a duplicate filename: {file_name}.")

        configs = []
        for config_name in config_names:
            config_path = file_path.with_name(config_name)
            if config_path.exists():
                configs.append(config_path)
        if len(configs) > 1:
            raise RuntimeError(
                f"Found a multiple config files in : {file_path.parent}."
            )
        file_sets.append(
            (file_path, out_path, configs[0] if len(configs) > 0 else None)
        )

    print("Found the following files to process:")
    for ii, (in_path, out_path, config_path) in enumerate(file_sets):
        print(f"  {ii + 1}: {in_path}")

    # Load any main config or cli args into new_args
    new_args: list[str] = []
    for action in parse_fields(bulk_cls):
        value = getattr(process_args, action.dest)
        if action.is_default(value):
            continue
        if action.dest in ["interactive", "in_path", "out_path", "config_name"]:
            continue
        new_args.extend(action.to_cli(value))

    if isinstance(args_class, NoInteractiveArgs):
        new_args.append("--no-interactive")

    input_cli_name = None
    output_cli_name = None
    for f in fields(args_class):
        if f.name in [input_arg_name, output_arg_name]:
            a = Action.from_field(f)
            assert a is not None
            if f.name == input_arg_name:
                input_cli_name = a.get_cli_option()
            else:
                output_cli_name = a.get_cli_option()
        elif input_cli_name is not None and output_cli_name is not None:
            break
        else:
            continue
    assert input_cli_name is not None
    assert output_cli_name is not None

    for ii, (in_path, out_path, config_path) in enumerate(file_sets):
        # Add the input and output file args and specific config file, if appropriate.
        basic_args = [
            input_cli_name,
            str(in_path),
            output_cli_name,
            str(out_path),
        ]
        if config_path is not None:
            basic_args.extend(["--config", str(config_path)])
        parser = argparse.ArgumentParser(prog=prog)
        add_arguments(parser, args_class)
        partial_args = args_class.parse_config(prog, args=[*basic_args, *new_args])
        parsed_args = parser.parse_args(args=partial_args.remaining_args)
        class_args = args_class(**vars(parsed_args))

        # Process the file specified
        print(f"Processing file {ii + 1}: {in_path}.")
        process_func(class_args, partial_args.config)
        print()
