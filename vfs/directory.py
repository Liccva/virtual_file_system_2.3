"""Каталог (Composite: Composite; Proxy: RealSubject)."""
from __future__ import annotations

from typing import Optional

from .errors import InvalidTreeOperationError
from .node import INDENT, FileSystemNode


class DirectoryComposite(FileSystemNode):
    def __init__(self, name: str) -> None:
        super().__init__(name)
        # Рекурсивная композиция: ребёнок - любой FileSystemNode
        # (файл, каталог, заместитель, ссылка). Тип ребёнка нигде не проверяется.
        self._children: list[FileSystemNode] = []

    @property
    def children(self) -> tuple[FileSystemNode, ...]:
        # Наружу отдаётся копия: менять состав можно только через add/remove.
        return tuple(self._children)

    # add/remove объявлены только здесь, а не в FileSystemNode
    # (вариант «безопасность»):
    # у файла не появляется бессмысленной операции «добавить ребёнка».
    def add(self, child: FileSystemNode) -> None:
        # Защита от цикла: нельзя поместить каталог в самого себя
        # или в своего потомка.
        # child.contains(self) истинно, если child - это self или его предок.
        if child.contains(self):
            raise InvalidTreeOperationError(
                f"Нельзя добавить '{child.name}' в '{self.name}': "
                f"каталог нельзя поместить в самого себя или в своего потомка"
            )
        if any(c.name == child.name for c in self._children):
            raise InvalidTreeOperationError(
                f"В каталоге '{self.name}' уже есть узел '{child.name}'"
            )
        self._children.append(child)

    def remove(self, child: FileSystemNode) -> None:
        if child not in self._children:
            raise InvalidTreeOperationError(
                f"Узел '{child.name}' не найден в каталоге '{self.name}'"
            )
        self._children.remove(child)

    def size(self) -> int:
        # Полиморфное делегирование детям - без проверки их типа.
        return sum(child.size() for child in self._children)

    def print_tree(self, depth: int = 0) -> str:
        # Каталог печатает только имя, без суммы размеров: иначе один закрытый
        # ребёнок (AccessDeniedError в size) оборвал бы печать всего дерева.
        lines = [f"{INDENT * depth}{self.name}/"]
        lines += [child.print_tree(depth + 1) for child in self._children]
        return "\n".join(lines)

    def find(self, name: str) -> Optional[FileSystemNode]:
        if self.name == name:
            return self
        for child in self._children:
            found = child.find(name)
            if found is not None:
                return found
        return None

    def contains(self, node: FileSystemNode) -> bool:
        return node is self or any(child.contains(node) for child in self._children)
