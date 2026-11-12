"""Символическая ссылка с контролем циклов (расширение 2.3.3)."""
from __future__ import annotations

from contextlib import contextmanager
from typing import Iterator, Optional

from .errors import VfsError
from .node import INDENT, FileSystemNode


class CycleDetectedError(VfsError):
    """Обход повторно вошёл в ту же ссылку - цикл."""


class SymbolicLink(FileSystemNode):
    """Ссылка на узел в другом месте дерева (заместитель цели).

    print_tree и find следуют за ссылкой; size() - нет: данные принадлежат цели,
    иначе они посчитались бы дважды (как du без -L).

    Контроль циклов: флаг «ссылка сейчас раскрывается». Каталог нельзя поместить
    в самого себя (DirectoryComposite.add), поэтому любой цикл проходит через
    ссылку, и повторный вход в ту же ссылку во время обхода означает цикл.
    """

    def __init__(self, name: str, target: FileSystemNode) -> None:
        super().__init__(name)
        self._target = target
        self._resolving = False

    @property
    def target(self) -> FileSystemNode:
        return self._target

    @contextmanager
    def _follow(self) -> Iterator[FileSystemNode]:
        if self._resolving:
            raise CycleDetectedError(
                f"Цикл ссылок: '{self.name}' -> '{self._target.name}'"
            )
        self._resolving = True
        try:
            yield self._target
        finally:
            self._resolving = False

    def size(self) -> int:
        return 0

    def print_tree(self, depth: int = 0) -> str:
        head = f"{INDENT * depth}{self.name} -> {self._target.name}"
        try:
            with self._follow() as target:
                return head + "\n" + target.print_tree(depth + 1)
        except CycleDetectedError:
            return head + " [цикл, не раскрывается]"

    def find(self, name: str) -> Optional[FileSystemNode]:
        if name == self.name:
            return self
        try:
            with self._follow() as target:
                return target.find(name)
        except CycleDetectedError:
            return None

    def contains(self, node: FileSystemNode) -> bool:
        # Ссылка не владеет целью: цель не входит в её поддерево.
        return node is self
