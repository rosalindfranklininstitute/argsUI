# SPDX-FileCopyrightText: 2026 Duncan McDougall <duncan.mcdougall@rfi.ac.uk>
#
# SPDX-License-Identifier: Apache-2.0
import itertools

import copy
from typing import Any, get_args, NamedTuple, Optional, Literal, Self, Type, TypeVar
import argparse
from dataclasses import field, Field, MISSING, fields, dataclass, is_dataclass
from enum import EnumType, Enum
import sys

from .extra_types import BaseType
from .dataclass_construct import build_dataclass_from_dict

from icecream import ic

T = TypeVar("T")

MISSING_TYPE = type(MISSING)

PossibleActions = Literal["store", "store_true", "store_false", "append"]


class ArgType(Enum):
    NOT_AN_ARG = 0
    AUTOMATIC = 1
    POSITIONAL = 2
    EXPLICIT_ONLY = 3


class PartialParsedArgs(NamedTuple):
    remaining_args: list[str]
    config: dict[str, Any]


def no_arg_field(**kw_args):
    kw_args.update(dict(metadata=dict(arg_type=ArgType.NOT_AN_ARG)))
    return field(**kw_args)


def arg_field(*args, arg_type: ArgType = ArgType.AUTOMATIC, defer=False, **kw_args):

    field_keys = (
        "default",
        "default_factory",
        "init",
        "repr",
        "hash",
        "compare",
        "metadata",
        "kw_only",
    )

    field_kw_args = {}

    for key in field_keys:
        if key in kw_args:
            field_kw_args[key] = kw_args[key]
            del kw_args[key]

    if "metadata" not in field_kw_args:
        field_kw_args["metadata"] = dict()

    if "doc" in kw_args:
        assert "help" not in kw_args
        if sys.version_info.minor < 14:
            field_kw_args["metadata"]["doc"] = kw_args["doc"]
            del kw_args["doc"]
    elif "help" in kw_args:
        assert "doc" not in kw_args
        if sys.version_info.minor < 14:
            field_kw_args["metadata"]["doc"] = kw_args["help"]
        else:
            kw_args["doc"] = kw_args["help"]
        del kw_args["help"]
    else:
        if sys.version_info.minor < 14:
            field_kw_args["metadata"]["doc"] = ""
        else:
            kw_args["doc"] = ""

    #     field_kw_args.update(kw_args)
    # else:
    #     field_kw_args["metadata"] = kw_args

    field_kw_args["metadata"]["args"] = args
    field_kw_args["metadata"]["arg_type"] = arg_type
    field_kw_args["metadata"]["defer"] = defer
    field_kw_args["metadata"]["kw_args"] = kw_args

    if "action" in kw_args:
        action = kw_args["action"]
        if action == "store_true":
            field_kw_args["default"] = False
        elif action == "store_false":
            field_kw_args["default"] = True

    return field(**field_kw_args)


class Action:
    def __init__(self):
        self.aliases: list[str] = []

        self.arg_type: ArgType = ArgType.AUTOMATIC
        self.defer: bool = False

        self.action: PossibleActions = "store"
        self.value_type: Any | MISSING_TYPE = MISSING
        self.help: str | MISSING_TYPE = MISSING
        self.default: Any | MISSING_TYPE = MISSING
        self.const: Any | MISSING_TYPE = MISSING
        self.nargs: None | str | int = None
        self.choices: list[Any] | None = None
        self.required: bool = False
        self.dest: str = ""
        self.metavar: str | tuple[str] | None = None
        self.extra_kw_args: dict[str, Any] = dict()

        self.is_parent: bool = False
        self.children: list["Action"] = []

        self.has_appending_parent: bool = False

    def __getitem__(self, index):
        match index:
            case "aliases":
                return self.aliases
            case "arg_type":
                return self.arg_type
            case "defer":
                return self.defer
            case "action":
                return self.action
            case "value_type":
                return self.value_type
            case "help":
                return self.help
            case "default":
                return self.default
            case "const":
                return self.const
            case "nargs":
                return self.nargs
            case "choices":
                return self.choices
            case "required":
                return self.required
            case "dest":
                return self.dest
            case "metavar":
                return self.metavar
            case "extra_kw_args":
                return self.extra_kw_args
            case _:
                raise ValueError(f"Unknown value for [{index}]")

    def fields(self) -> tuple[str, ...]:
        return (
            "aliases",
            "arg_type",
            "defer",
            "action",
            "value_type",
            "help",
            "default",
            "const",
            "nargs",
            "choices",
            "required",
            "dest",
            "metavar",
            "extra_kw_args",
        )

    def __repr__(self) -> str:
        parts = []
        for k in self.fields():
            parts.append(f"{k}={self[k]}")
        return f"Action( {', '.join(parts)})"

    def _to_append_argument_kwargs(self) -> dict[str, Any]:
        result: dict[str, Any] = {}

        def add_if_not(key, filter_value):
            if self[key] != filter_value:
                result[key] = self[key]

        result["dest"] = self.dest

        match self.action:
            case "store_true" | "store_false":
                result["const"] = self.action == "store_true"
                result["action"] = "append_const"
            case "append" | "extend" | "append_const":
                raise RuntimeError("We should not get here.")
            case "store":
                if self.value_type != MISSING:
                    result["type"] = self.value_type
                result["action"] = "append"
            case "store_const":
                result["const"] = self.const
                result["action"] = "append_const"
            case _:
                raise NotImplementedError(
                    f"{self.action} not implemented for subfieds of an appending parent."
                )

        add_if_not("help", MISSING)
        add_if_not("nargs", None)
        add_if_not("choices", None)
        add_if_not("metavar", None)
        for k, v in self.extra_kw_args.items():
            result[k] = v

        return result

    def _to_argument_kwargs(self) -> dict[str, Any]:
        result: dict[str, Any] = dict(action=self.action)

        def add_if_not(key, filter_value):
            if self[key] != filter_value:
                result[key] = self[key]

        if self.value_type != MISSING:
            result["type"] = self.value_type

        if self.arg_type != ArgType.POSITIONAL:
            result["dest"] = self.dest
            result["required"] = self.required

        if self.help != MISSING and self.default != MISSING:
            result["help"] = f"{self.help} Default '{self.default}'."
        else:
            add_if_not("help", MISSING)

        add_if_not("default", MISSING)
        add_if_not("const", MISSING)

        add_if_not("nargs", None)
        add_if_not("choices", None)
        add_if_not("metavar", None)
        for k, v in self.extra_kw_args.items():
            result[k] = v
        return result

    def get_default_aliase(self) -> str:
        return self.aliases[-1]

    def get_display_name(self) -> str:
        return self.get_default_aliase().strip("-").replace("-", " ")

    # def is_boolean(self) -> bool:
    #     return self.action in ["store_true", "store_false"]

    def is_default(self, value) -> bool:
        """
        Is the given value the default value.
        """
        return self.default == value

    def get_default(self) -> Any:
        if self.default == MISSING:
            if self.action in ["store_true", "store_false"]:
                return self.action == "store_false"
            else:
                raise ValueError("Missing default requested.")
        return self.default

    def _value_to_str(self, value):
        match type(value):
            case EnumType():
                return str(value.value)
            case str():
                return value
            case _:
                return str(value)

    def to_cli(self, value) -> list[str]:
        match self.action:
            case "store_true":
                assert isinstance(value, bool)
                return [self.get_default_aliase()] if value else []
            case "store_false":
                assert isinstance(value, bool)
                return [self.get_default_aliase()] if not value else []
            case "append":
                results = []
                for inner_value in value:
                    if self.nargs is not None:
                        results.extend(
                            [
                                self.get_default_aliase(),
                                *[self._value_to_str(v) for v in inner_value],
                            ]
                        )
                    else:
                        results.extend(
                            [self.get_default_aliase(), self._value_to_str(inner_value)]
                        )
                return results
            case _:
                if self.nargs is not None:
                    return [
                        self.get_default_aliase(),
                        *[self._value_to_str(v) for v in value],
                    ]
                else:
                    return [self.get_default_aliase(), self._value_to_str(value)]

    def _child_alaises(
        self, short_aliases: list[str], long_aliases: list[str], child: "Action"
    ) -> list[str]:
        child_short_aliases = [
            a.strip("-") for a in child.aliases if a[0] == "-" and a[1] != "-"
        ]
        child_long_aliases = [a.strip("-") for a in child.aliases if a[0:2] == "--"]

        aliases = [
            f"{outer}.{inner}"
            for outer, inner in itertools.product(short_aliases, child_short_aliases)
        ]
        aliases.extend(
            [
                f"{outer}.{inner}"
                for outer, inner in itertools.product(long_aliases, child_long_aliases)
            ]
        )
        return aliases

    def all_aliases(self) -> list[str]:
        if not self.is_parent:
            return self.aliases
        else:
            short_aliases = [a for a in self.aliases if a[0] == "-" and a[1] != "-"]
            long_aliases = [a for a in self.aliases if a[0:2] == "--"]
            aliases = []
            for child in self.children:
                aliases.extend(self._child_alaises(short_aliases, long_aliases, child))
            return aliases

    def add_to_parser(self, parser, override_alaises: list[str] | None = None) -> list:
        results = []
        aliases = self.aliases if override_alaises is None else override_alaises
        if not self.is_parent:
            if self.has_appending_parent:
                results.append(
                    parser.add_argument(*aliases, **self._to_append_argument_kwargs())
                )
            else:
                results.append(
                    parser.add_argument(*aliases, **self._to_argument_kwargs())
                )
        else:
            short_aliases = [a for a in aliases if a[0] == "-" and a[1] != "-"]
            long_aliases = [a for a in aliases if a[0:2] == "--"]
            for child in self.children:
                child_aliases = self._child_alaises(short_aliases, long_aliases, child)
                results.extend(child.add_to_parser(parser, child_aliases))
        return results

    def dist_dict(self) -> dict[str, Any]:
        if not self.is_parent:
            return {self.dest: self}
        else:
            result = {}
            for child in self.children:
                result.update(child.dist_dict())
            return result


class ActionList(list[Action]):
    def aliase_dict(self, include_short: bool = False) -> dict[str, Action]:
        result: dict[str, Action] = {}
        for a in self:
            a_dict = {
                name.strip("-"): a
                for name in a.all_aliases()
                if include_short or name.startswith("--")
            }
            result.update(a_dict)
        return result

    def dist_dict(self, include_short: bool = False) -> dict[str, Action]:
        result: dict[str, Action] = {}
        for a in self:
            a_dict = a.dist_dict()
            result.update(a_dict)
        return result


def _process_root_action(action, kw_args) -> Action:
    match action.action:
        case "store_true" | "store_false":
            action.default = MISSING
            action.value_type = MISSING
            if "nargs" in kw_args:
                raise TypeError(
                    "nargs cannot be specified with action=store_true | store_false"
                )
            if "const" in kw_args:
                raise TypeError(
                    "const cannot be specified with action=store_true | store_false"
                )
        case "store_const":
            if "nargs" in kw_args:
                raise TypeError(
                    "nargs cannot be specified with action=store_true | store_false"
                )
            action.value_type = MISSING
        case "append":
            inner_type = get_args(action.value_type)
            if len(inner_type) != 1:
                raise TypeError(
                    f"Expected {action.dest} to have a single nested type, but found {len(inner_type)} for type {action.value_type}"
                )
            action.value_type = inner_type[0]
        case _:
            pass
    return action


def _check_child_action(action, kw_args):
    if isinstance(action.nargs, str) and (action.nargs == "*" or action.nargs == "+"):
        raise TypeError("variable nargs cannot be specified on a child property.")


def _check_nested_append_action(parent, action, kw_args):
    if action.required:
        raise NotImplementedError("Required nested fields are not supported.")

    match action.action:
        case "append" | "extend" | "append_const":
            raise NotImplementedError(
                f"{action.action} on nested fields is not supported."
            )
        case _:
            pass


def _root(
    fld: Field, parent: Action | None, appending_parent: bool
) -> Optional[Action]:
    try:
        if "arg_type" not in fld.metadata:
            return None
        elif fld.metadata["arg_type"] == ArgType.NOT_AN_ARG:
            return None

        action = Action()

        # default
        # default_factory
        if fld.default != MISSING:
            assert fld.default_factory == MISSING
            action.default = fld.default
        elif fld.default_factory != MISSING:
            assert fld.default == MISSING
            action.default = fld.default_factory()
        else:
            action.default = MISSING

        # init
        # repr
        # hash
        # compare
        # kw_only
        # -> ignore
        # doc
        assert sys.version_info.major == 3
        if sys.version_info.minor < 14:
            action.help = fld.metadata["doc"]
        else:
            action.help = fld.doc

        # metadata
        action.aliases = list(fld.metadata["args"])
        action.arg_type = fld.metadata["arg_type"]
        action.defer = fld.metadata["defer"]

        if parent is not None and action.arg_type != ArgType.AUTOMATIC:
            raise TypeError("arg_type must be AUTOMATIC fro nested fields.")

        match action.arg_type:
            case ArgType.POSITIONAL:
                assert len(action.aliases) == 0
                action.aliases.append(f"{fld.name.replace('_', '-')}")
            case ArgType.AUTOMATIC:
                action.aliases.append(f"--{fld.name.replace('_', '-')}")
            case ArgType.EXPLICIT_ONLY:
                pass

        if parent is not None:
            action.dest = f"{parent.dest}.{fld.name}"
        else:
            action.dest = fld.name

        kw_args = copy.copy(fld.metadata["kw_args"])
        action.action = kw_args.get("action", "store")

        if "type" in kw_args:
            action.value_type = kw_args["type"]
            del kw_args["type"]

        else:
            action.value_type = fld.type

        action = _process_root_action(action, kw_args)

        action.nargs = kw_args.get("nargs", None)
        if isinstance(action.nargs, int):
            nargs_more_than_one = action.nargs > 1
        elif isinstance(action.nargs, str):
            nargs_more_than_one = action.nargs == "*" or action.nargs == "+"
        else:
            nargs_more_than_one = False

        if nargs_more_than_one:
            inner_type = get_args(action.value_type)
            if len(inner_type) != 1:
                raise TypeError(
                    f"Expected {action.dest} to have a single nested type, but found {len(inner_type)} for type {action.value_type}"
                )
            action.value_type = inner_type[0]

        if parent is not None:
            _check_child_action(action, kw_args)

        if appending_parent:
            _check_nested_append_action(parent, action, kw_args)
            action.has_appending_parent = True

        if is_dataclass(action.value_type):
            appending_parent = appending_parent or (action.action == "append")
            action.children = _children(fld, action, appending_parent, kw_args)
            action.is_parent = True
            return action
        else:
            return _single(fld, action, kw_args)

    except BaseException as e:
        raise e
    raise RuntimeError(f"Could not process field '{fld.name}'") from e


def _children(
    fld: Field, action: Action, appending_parent: bool, kw_args
) -> list[Action]:
    if action.action not in ("store", "append"):
        raise TypeError("Dataclasses can only be stored or appended")
    invalid_nargs = False
    if isinstance(action.nargs, int):
        invalid_nargs = action.nargs > 1
    elif action.nargs is not None:
        invalid_nargs = True
    if invalid_nargs:
        raise TypeError("multiple nargs cannot be specified with a nested class.")
    if "choices" in kw_args:
        raise TypeError("choices cannot be specified with a nested class.")
    if action.arg_type != ArgType.AUTOMATIC:
        raise TypeError("arg_type must be AUTOMATIC for nested classes.")

    return [
        a
        for a in [_root(f, action, appending_parent) for f in fields(action.value_type)]
        if a is not None
    ]


def _single(fld: Field, action: Action, kw_args) -> Action:

    if isinstance(action.value_type, BaseType):
        if action.value_type.get_type() is not fld.type:
            raise TypeError(
                f'Expected "{fld.name}" of type {action.value_type} to be {action.value_type.get_type()} but found {fld.type}'
            )
    if isinstance(action.value_type, EnumType):
        members = set(list(action.value_type))
        if "choices" in kw_args:
            if not set(kw_args["choices"]) <= members:
                raise TypeError(
                    f"Expected choices of '{action.dest}' to be a subset of the Enum {action.value_type}"
                )
            action.choices = kw_args["choices"]
            del kw_args["choices"]
        else:
            action.choices = list(action.value_type)
    else:
        action.choices = kw_args.get("choices", None)

    if (
        action.choices is not None
        and action.default != MISSING
        and action.default not in action.choices
    ):
        raise TypeError(
            f"Expected '{action.default}' to be a valid choice for '{action.dest}'"
        )

    if action.arg_type == ArgType.POSITIONAL:
        assert kw_args.get("required", False) is False
    action.required = kw_args.get("required", False)
    action.metavar = kw_args.get("metavar", None)
    action.const = kw_args.get("const", MISSING)

    for name in action.fields():
        if name in kw_args:
            del kw_args[name]
    action.extra_kw_args = kw_args

    return action


def from_field(fld: Field) -> Optional[Action]:
    return ic(_root(fld, parent=None, appending_parent=False))


def from_dataclass(dcls) -> ActionList:
    return ActionList(
        [f for f in [from_field(f) for f in fields(dcls)] if f is not None]
    )


def add_arguments(parser: argparse.ArgumentParser, dcls: type | list[Action]):
    if isinstance(dcls, type):
        actions = from_dataclass(dcls)
    else:
        actions = dcls
    defered = []
    for a in actions:
        if a.defer:
            defered.append(a)
        else:
            a.add_to_parser(parser)
    for a in defered:
        a.add_to_parser(parser)


def _recursively_group_and_invert(evaluation_dict, actions, prefix):
    dest_to_action = {a.dest[len(prefix) :]: a for a in actions}
    dest_to_sub_dict = {}
    keys_to_reevaluate = set()

    for k, v in evaluation_dict.items():
        parts = k.split(sep=".", maxsplit=1)
        action = dest_to_action[parts[0]]
        if len(parts) > 1 and not action.is_parent:
            raise RuntimeError("We should never get here.")
        if action.is_parent:
            if len(parts) != 2:
                raise RuntimeError("We should never get here.")

            if parts[0] not in dest_to_sub_dict:
                dest_to_sub_dict[parts[0]] = {}
            dest_to_sub_dict[parts[0]][parts[1]] = v
            keys_to_reevaluate.add(parts[0])
        else:
            dest_to_sub_dict[parts[0]] = v

    for k in keys_to_reevaluate:
        action = dest_to_action[k]
        sub_dict = dest_to_sub_dict[k]
        if action.action == "append":
            lengths = [len(v) for v in sub_dict.values()]
            assert len(lengths) > 0
            max_len = max(lengths)
            inverted_dict: list[dict[str, Any]] = [{} for _ in range(max_len)]
            for sub_k, v in sub_dict.items():
                for ii, vv in enumerate(v):
                    inverted_dict[ii][sub_k] = vv

            dest_to_sub_dict[k] = [
                _recursively_group_and_invert(inv, action.children, f"{prefix}{k}.")
                for inv in inverted_dict
            ]
        else:
            dest_to_sub_dict[k] = _recursively_group_and_invert(
                sub_dict, action.children, f"{prefix}{k}."
            )
    return dest_to_sub_dict


def from_arguments(args: argparse.Namespace, dcls: Type[T]) -> T:
    actions = from_dataclass(dcls)

    data_dict = _recursively_group_and_invert(vars(args), actions, "")

    return build_dataclass_from_dict(dcls, data_dict)
