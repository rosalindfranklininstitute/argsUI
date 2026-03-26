<!--
SPDX-FileCopyrightText: 2026 Duncan McDougall <duncan.mcdougall@rfi.ac.uk>

SPDX-License-Identifier: Apache-2.0
-->

# Data Args
Library for turining dataclasses into argparserr args and gui.
Inspired by (datargs)[https://github.com/roee30/datargs.git] and (mininterface)[https://github.com/CZ-NIC/mininterface.git].

This version is, curretly, more janky. 
But it add some missing features.

# Features

- Ignore normal fields, only parse `arg_field`s
- Allow "append" action.
- Read options from toml config file, before the command line, allowing long commands to be stored in file.
- Display command as an interative plot based on a cli flag.
- Allow overriding options at each stage.
- Allow required options to be defered to the GUI.

# Option priorities
- First the config file is read, if present.
- Then the command line options are read, potentially overriding any settings in the config file.
- Then the GUI is preseted (if requested) showing all the values as set.
