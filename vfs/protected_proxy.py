"""Защищающий заместитель (Proxy: Protection Proxy)."""
from __future__ import annotations

from typing import Optional

from .access import AccessService, Permission, User
from .errors import AccessDeniedError
from .node import INDENT, FileSystemNode


class ProtectedNodeProxy(FileSystemNode):
    """Стоит в дереве на месте реального узла и реализует тот же контракт.

    Права проверяются ДО делегирования; при отказе subject не вызывается,
    поэтому его размер и дети не раскрываются. Сам прокси о структуре
    дерева ничего не знает - это ответственность Composite.
    """

    def __init__(self, subject: FileSystemNode, access: AccessService,
                 user: User) -> None:
        super().__init__(subject.name)  # имя видно в листинге родителя
        self._subject = subject
        self._access = access
        self._user = user

    def _allowed(self, permission: Permission) -> bool:
        return self._access.is_allowed(self._user, self._subject, permission)

    def size(self) -> int:
        # Точная величина: частичный результат был бы незаметно неверным,
        # поэтому при отказе - понятная ошибка, а не 0.
        if not self._allowed(Permission.READ):
            raise AccessDeniedError(self._user.name, self.name, Permission.READ)
        return self._subject.size()

    def print_tree(self, depth: int = 0) -> str:
        # Навигация: закрытая часть заменяется пометкой,
        # остальное дерево печатается.
        # Сначала LIST; если его нет, READ уже не проверяется
        # (короткое замыкание and).
        if not (self._allowed(Permission.LIST) and self._allowed(Permission.READ)):
            return f"{INDENT * depth}{self.name} [нет доступа]"
        return self._subject.print_tree(depth)

    def find(self, name: str) -> Optional[FileSystemNode]:
        # Совпало имя - возвращаем сам прокси, а не subject:
        # иначе клиент получил бы ссылку в обход проверки прав.
        if name == self.name:
            return self
        # Без LIST поиск внутрь не идёт и не сообщает, есть ли там такой узел.
        if not self._allowed(Permission.LIST):
            return None
        return self._subject.find(name)

    def contains(self, node: FileSystemNode) -> bool:
        return node is self or self._subject.contains(node)
