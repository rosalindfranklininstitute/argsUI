<!--
SPDX-FileCopyrightText: 2026 Duncan McDougall <duncan.mcdougall@rfi.ac.uk>

SPDX-License-Identifier: Apache-2.0
-->

# Args UI
![argsui-version](https://raw.githubusercontent.com/rosalindfranklininstitute/argsUI/raw/refs/heads/badges/badges/argsui-version.svg)
![argsui-requires-python](https://raw.githubusercontent.com/rosalindfranklininstitute/argsUI/raw/refs/heads/badges/badges/argsui-requires-python.svg)

![tests](https://raw.githubusercontent.com/rosalindfranklininstitute/argsUI/raw/refs/heads/badges/badges/tests.svg)
![skipped](https://raw.githubusercontent.com/rosalindfranklininstitute/argsUI/raw/refs/heads/badges/badges/skipped.svg)
![coverage](https://raw.githubusercontent.com/rosalindfranklininstitute/argsUI/raw/refs/heads/badges/badges/coverage.svg)
![last-run](https://raw.githubusercontent.com/rosalindfranklininstitute/argsUI/raw/refs/heads/badges/badges/last-run.svg)

Library for turning dataclasses into argparser args and gui.
Inspired by [datargs](https://github.com/roee30/datargs.git) and [mininterface](https://github.com/CZ-NIC/mininterface.git).

# Features

- Ignore normal fields, only parse `arg_field`s
- Allow "append" action.
- Allow nested data classes
- Provides some useful utilities

# Utilities

- `config_args` allows reading arguments from a toml file.
- `interactive_args` allows displaying the arguments as a GUI.
- `bulk_args` allows wrapping a single file CLI into a recursive multi file CLI.
- All of these can easily be composed, and the arguments (fields of the dataclass) filled in progressively, or overridden, at each stage.


