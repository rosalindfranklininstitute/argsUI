# SPDX-FileCopyrightText: 2026 Duncan McDougall <duncan.mcdougall@rfi.ac.uk>
#
# SPDX-License-Identifier: Apache-2.0

import argparse
from dataclasses import dataclass
import logging


import argsui as dargs
from argsui import InteractiveArgs, from_dataclass

try:
    from PySide6 import QtWidgets, QtCore

    def test_bool(qtbot):

        @dataclass
        class BoolOptions(InteractiveArgs):
            store_true: bool = dargs.arg_field(action="store_true")
            store_false: bool = dargs.arg_field(action="store_false")

        actions = from_dataclass(BoolOptions)

        window = BoolOptions.create_window("test", actions, [], [])
        qtbot.addWidget(window)

        assert window.layout().rowCount() == 2 + 1
        for i in range(2):
            widget = window.layout().itemAtPosition(i, 0).widget()
            assert isinstance(widget, QtWidgets.QCheckBox)
            if widget.text() == "store true":
                assert not widget.isChecked()
            else:
                assert widget.isChecked()

        window.show()
        assert window.isVisible()

        window.btn_ok.click()

        def is_closed():
            assert not window.isVisible()

        qtbot.waitUntil(is_closed, timeout=500)

        assert window.result_values["store_true"] is False
        assert window.result_values["store_false"] is True

        window = BoolOptions.create_window("test", actions, [], [])
        qtbot.addWidget(window)

        assert window.layout().rowCount() == 2 + 1
        for i in range(2):
            widget = window.layout().itemAtPosition(i, 0).widget()
            assert isinstance(widget, QtWidgets.QCheckBox)
            widget.toggle()

        window.show()
        assert window.isVisible()

        window.btn_ok.click()

        qtbot.waitUntil(is_closed, timeout=500)

        assert window.result_values["store_true"] is True
        assert window.result_values["store_false"] is False

    def test_fancy_bool(qtbot):

        @dataclass
        class BoolOptions(InteractiveArgs):
            first: bool = dargs.arg_field(
                action=argparse.BooleanOptionalAction, default=True
            )
            second: bool = dargs.arg_field(
                action=argparse.BooleanOptionalAction, default=False
            )
            third: bool = dargs.arg_field(
                action=argparse.BooleanOptionalAction, default=None
            )

        actions = from_dataclass(BoolOptions)

        window = BoolOptions.create_window("test", actions, [], [])
        qtbot.addWidget(window)

        assert window.layout().rowCount() == 3 + 1
        for i in range(3):
            widget = window.layout().itemAtPosition(i, 0).widget()
            assert isinstance(widget, QtWidgets.QCheckBox)
            match i:
                case 0:
                    assert widget.text() == "first"
                    assert widget.isChecked()
                case 1:
                    assert widget.text() == "second"
                    assert not widget.isChecked()
                case 2:
                    assert widget.text() == "third"
                    assert widget.checkState() == QtCore.Qt.PartiallyChecked

        window.show()
        assert window.isVisible()

        window.btn_ok.click()

        def is_closed():
            assert not window.isVisible()

        qtbot.waitUntil(is_closed, timeout=500)

        assert window.result_values["first"] is True
        assert window.result_values["second"] is False
        assert window.result_values["third"] is None

except ImportError:
    logging.getLogger(__name__).warning(
        "Failed to import PySide6. InteractiveArgs will not work as expected"
    )
