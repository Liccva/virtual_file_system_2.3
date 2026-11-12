"""Сервис прав: пользователь, права и политика доступа."""
from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from enum import Enum

from .node import FileSystemNode


class Permission(Enum):
    READ = "read"  # размер и содержимое узла
    LIST = "list"  # структура: печать дерева, поиск внутри


@dataclass(frozen=True)
class User:
    id: str
    name: str


class AccessService(ABC):
    """Отвечает на вопрос: может ли пользователь выполнить действие над узлом."""

    @abstractmethod
    def is_allowed(self, user: User, node: FileSystemNode,
                   permission: Permission) -> bool:
        ...


class AclAccessService(AccessService):
    """Список доступа (ACL). По умолчанию всё запрещено."""

    def __init__(self) -> None:
        self._acl: dict[FileSystemNode, dict[str, set[Permission]]] = {}

    def grant(self, user: User, node: FileSystemNode,
              *permissions: Permission) -> None:
        rights = self._acl.setdefault(node, {}).setdefault(user.id, set())
        rights.update(permissions)

    def is_allowed(self, user: User, node: FileSystemNode,
                   permission: Permission) -> bool:
        return permission in self._acl.get(node, {}).get(user.id, set())
