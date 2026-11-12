"""Удалённые файлы: ленивая загрузка и кэш метаданных (расширение 2.3.3)."""
from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Optional

from .errors import VfsError
from .node import INDENT, FileSystemNode


class RemoteStorageError(VfsError):
    """Удалённый объект недоступен."""


@dataclass(frozen=True)
class RemoteMetadata:
    size: int


class RemoteStorage(ABC):
    """Клиент удалённого хранилища."""

    @abstractmethod
    def fetch_metadata(self, path: str) -> RemoteMetadata:
        ...


class InMemoryRemoteStorage(RemoteStorage):
    """Заглушка сервера без сети: хранит объекты в памяти и журналирует запросы."""

    def __init__(self, objects: Optional[dict[str, int]] = None) -> None:
        self._objects = dict(objects or {})
        self.requests: list[str] = []

    def put(self, path: str, size: int) -> None:
        self._objects[path] = size

    def fetch_metadata(self, path: str) -> RemoteMetadata:
        self.requests.append(path)
        if path not in self._objects:
            raise RemoteStorageError(f"Удалённый объект '{path}' не найден")
        return RemoteMetadata(size=self._objects[path])


class LazyRemoteFileProxy(FileSystemNode):
    """Виртуальный заместитель удалённого файла с кэшем метаданных.

    При создании ничего не загружает. Первое обращение к size/print_tree
    загружает метаданные, повторные берут их из кэша. Проверку прав выполняет
    внешний ProtectedNodeProxy: цепочка Protected(Lazy) гарантирует,
    что при отказе до загрузки дело не доходит.
    """

    def __init__(self, name: str, storage: RemoteStorage, remote_path: str) -> None:
        super().__init__(name)
        self._storage = storage
        self._remote_path = remote_path
        self._metadata: Optional[RemoteMetadata] = None

    @property
    def is_loaded(self) -> bool:
        return self._metadata is not None

    def _load(self) -> RemoteMetadata:
        if self._metadata is None:
            # Ошибка загрузки не кэшируется: следующее обращение повторит запрос.
            self._metadata = self._storage.fetch_metadata(self._remote_path)
        return self._metadata

    def size(self) -> int:
        return self._load().size

    def print_tree(self, depth: int = 0) -> str:
        return f"{INDENT * depth}{self.name} ({self.size()} B) [remote]"

    def find(self, name: str) -> Optional[FileSystemNode]:
        # Поиск по имени не требует загрузки.
        return self if self.name == name else None

    def contains(self, node: FileSystemNode) -> bool:
        return node is self
