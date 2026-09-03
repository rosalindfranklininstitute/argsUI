# SPDX-FileCopyrightText: 2026 Duncan McDougall <duncan.mcdougall@rfi.ac.uk>
#
# SPDX-License-Identifier: Apache-2.0

from abc import ABC, abstractmethod
from pathlib import Path


class BaseType(ABC):
    @abstractmethod
    def get_type(self) -> type:
        pass


class FilePathType(BaseType):
    def __init__(self, must_exist: bool):
        self.must_exist = must_exist

    def __call__(self, path: str) -> Path:
        result = Path(path)

        if result.is_file():
            return result
        if result.exists():
            raise TypeError(f"{path} is not a file.")
        if self.must_exist:
            raise TypeError(f"{path} does not exist.")
        return result

    def __repr__(self) -> str:
        return f"FilePath(must_exist={self.must_exist})"

    def get_type(self) -> type[Path]:
        return Path


class DirPathType(BaseType):
    def __init__(self, must_exist: bool):
        self.must_exist = must_exist

    def __call__(self, path: str) -> Path:
        result = Path(path)

        if result.is_dir():
            return result
        if result.exists():
            raise TypeError(f"{path} is not a file.")
        if self.must_exist:
            raise TypeError(f"{path} does not exist.")
        return result

    def __repr__(self) -> str:
        return f"DirPath(must_exist={self.must_exist})"

    def get_type(self) -> type[Path]:
        return Path
