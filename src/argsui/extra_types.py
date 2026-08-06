# SPDX-FileCopyrightText: 2026 Duncan McDougall <duncan.mcdougall@rfi.ac.uk>
#
# SPDX-License-Identifier: Apache-2.0

from pathlib import Path
from abc import ABC, abstractmethod


class BaseType(ABC):
    @abstractmethod
    def get_type(self):
        pass


class FilePathType(BaseType):
    def __init__(self, must_exist: bool):
        self.must_exist = must_exist

    def __call__(self, path: str) -> Path:
        result = Path(path)

        if result.is_file():
            return result
        elif result.exists():
            raise TypeError(f"{path} is not a file.")
        elif self.must_exist:
            raise TypeError(f"{path} does not exist.")
        else:
            return result

    def __repr__(self) -> str:
        return f"FilePath(must_exist={self.must_exist})"

    def get_type(self):
        return Path


class DirPathType(BaseType):
    def __init__(self, must_exist: bool):
        self.must_exist = must_exist

    def __call__(self, path: str) -> Path:
        result = Path(path)

        if result.is_dir():
            return result
        elif result.exists():
            raise TypeError(f"{path} is not a file.")
        elif self.must_exist:
            raise TypeError(f"{path} does not exist.")
        else:
            return result

    def __repr__(self) -> str:
        return f"DirPath(must_exist={self.must_exist})"

    def get_type(self):
        return Path
