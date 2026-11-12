"""Тестовые двойники: шпионы для проверки взаимодействия и порядка вызовов."""
from __future__ import annotations

from vfs.access import AccessService, Permission
from vfs.node import FileSystemNode


class RecordingAccess(AccessService):
    """Разрешает заданные права и пишет каждую проверку в общий журнал."""

    def __init__(self, log: list[str], allowed: set[Permission]) -> None:
        self.log = log
        self.allowed = allowed

    def is_allowed(self, user, node, permission) -> bool:
        self.log.append(f"check {permission.name}")
        return permission in self.allowed


class RecordingNode(FileSystemNode):
    """Реальный узел-шпион: пишет в журнал каждое обращение к нему."""

    def __init__(self, name: str, log: list[str], size: int = 42) -> None:
        super().__init__(name)
        self.log = log
        self._size = size

    def size(self) -> int:
        self.log.append("subject.size")
        return self._size

    def print_tree(self, depth: int = 0) -> str:
        self.log.append("subject.print_tree")
        return f"{self.name} ({self._size} B)"

    def find(self, name: str):
        self.log.append("subject.find")
        return None

    def contains(self, node) -> bool:
        return node is self
