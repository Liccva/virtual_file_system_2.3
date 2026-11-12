"""Общий контракт узла дерева.

Роль в шаблонах: Composite - Component, Proxy - Subject.
Клиент работает только с этим типом и не знает, что перед ним:
файл, каталог, заместитель или ссылка.
"""
from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Optional

INDENT = "  "


class FileSystemNode(ABC):
    def __init__(self, name: str) -> None:
        if not name:
            raise ValueError("Имя узла не может быть пустым")
        self._name = name

    @property
    def name(self) -> str:
        return self._name

    @abstractmethod
    def size(self) -> int:
        """Размер в байтах (для каталога - сумма по поддереву)."""

    @abstractmethod
    def print_tree(self, depth: int = 0) -> str:
        """Текстовое представление поддерева с отступом depth."""

    @abstractmethod
    def find(self, name: str) -> Optional[FileSystemNode]:
        """Первый узел с данным именем в поддереве (поиск в глубину) или None."""

    @abstractmethod
    def contains(self, node: FileSystemNode) -> bool:
        """Служебная проверка: входит ли node в поддерево (включая сам узел).

        Нужна DirectoryComposite.add для защиты от циклов; права не проверяет.
        """

    def __repr__(self) -> str:
        return f"{type(self).__name__}({self._name!r})"
