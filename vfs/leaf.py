"""Файл - лист дерева (Composite: Leaf; Proxy: RealSubject)."""
from __future__ import annotations

from typing import Optional

from .node import INDENT, FileSystemNode


class FileLeaf(FileSystemNode):
    def __init__(self, name: str, size_bytes: int) -> None:
        super().__init__(name)
        if size_bytes < 0:
            raise ValueError(f"Размер файла '{name}' не может быть отрицательным")
        self._size = size_bytes

    def size(self) -> int:
        return self._size

    def print_tree(self, depth: int = 0) -> str:
        return f"{INDENT * depth}{self.name} ({self._size} B)"

    def find(self, name: str) -> Optional[FileSystemNode]:
        return self if self.name == name else None

    def contains(self, node: FileSystemNode) -> bool:
        return node is self
