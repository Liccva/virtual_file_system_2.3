"""Точка сборки (composition root) и демонстрация.

Только здесь создаются конкретные классы и решается, какие узлы закрыть прокси.
Клиентский код (client) знает лишь FileSystemNode и AccessDeniedError.
"""
from __future__ import annotations

import sys
from types import SimpleNamespace

from vfs.access import AclAccessService, Permission, User
from vfs.directory import DirectoryComposite
from vfs.errors import AccessDeniedError, InvalidTreeOperationError
from vfs.leaf import FileLeaf
from vfs.node import FileSystemNode
from vfs.protected_proxy import ProtectedNodeProxy
from vfs.remote import InMemoryRemoteStorage, LazyRemoteFileProxy
from vfs.symlink import SymbolicLink

READ, LIST = Permission.READ, Permission.LIST
ADMIN = User("u0", "admin")
OLESYA = User("u1", "olesya")


# ----------------------------------------------------------------- сборка 2.3.2
def _build_base(access: AclAccessService, user: User) -> SimpleNamespace:
    root = DirectoryComposite("root")

    docs = DirectoryComposite("docs")
    docs.add(FileLeaf("report.docx", 120))
    docs.add(FileLeaf("notes.txt", 30))

    photos = DirectoryComposite("photos")
    photos.add(FileLeaf("cat.png", 2048))

    secret = DirectoryComposite("secret")
    secret.add(FileLeaf("passwords.txt", 300))
    access.grant(ADMIN, secret, READ, LIST)

    # Реальный secret в дерево напрямую не попадает - только через прокси.
    secret_proxy = ProtectedNodeProxy(secret, access, user)

    root.add(docs)
    root.add(photos)
    root.add(secret_proxy)
    return SimpleNamespace(root=root, docs=docs, secret_proxy=secret_proxy)


def build_base_tree(access: AclAccessService, user: User) -> FileSystemNode:
    return _build_base(access, user).root


# ------------------------------------------------------- сборка 2.3.3 (расширение)
def build_extended_tree(access: AclAccessService, user: User,
                        storage: InMemoryRemoteStorage) -> FileSystemNode:
    base = _build_base(access, user)

    # Удалённые файлы: Protected(Lazy) - права проверяются до загрузки.
    backup = LazyRemoteFileProxy("backup.zip", storage, "/backups/backup.zip")
    video = LazyRemoteFileProxy("video.mp4", storage, "/media/video.mp4")
    access.grant(ADMIN, backup, READ, LIST)
    access.grant(ADMIN, video, READ, LIST)
    access.grant(OLESYA, backup, READ, LIST)  # на video.mp4 у olesya прав нет

    cloud = DirectoryComposite("cloud")
    cloud.add(ProtectedNodeProxy(backup, access, user))
    cloud.add(ProtectedNodeProxy(video, access, user))
    base.root.add(cloud)

    # Ссылки: на собственный каталог (цикл) и на защищённый узел (ссылка ведёт
    # на прокси, поэтому через неё проверка прав не обходится).
    base.docs.add(SymbolicLink("loop", base.docs))
    base.root.add(SymbolicLink("secret_link", base.secret_proxy))
    return base.root


# ---------------------------------------------------------------- клиент
def client(root: FileSystemNode) -> None:
    """Клиентский сценарий: одинаковый до и после расширения."""
    print(root.print_tree())
    try:
        print(f"Размер дерева: {root.size()} B")
    except AccessDeniedError as error:
        print(f"Ошибка: {error}")
    found = root.find("passwords.txt")
    print(f"find('passwords.txt'): {'найден' if found else 'не найден'}")


def demo_tree_errors() -> None:
    a = DirectoryComposite("a")
    b = DirectoryComposite("b")
    a.add(b)
    for parent, child in ((a, a), (b, a)):
        try:
            parent.add(child)
        except InvalidTreeOperationError as error:
            print(f"Ошибка: {error}")


def main() -> None:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")

    print("=== До расширения (2.3.2) ===")
    for user in (OLESYA, ADMIN):
        print(f"\n--- пользователь {user.name} ---")
        client(build_base_tree(AclAccessService(), user))

    print("\n=== Ошибки структуры ===")
    demo_tree_errors()

    print("\n=== После расширения (2.3.3) ===")
    for user in (OLESYA, ADMIN):
        print(f"\n--- пользователь {user.name} ---")
        storage = InMemoryRemoteStorage(
            {"/backups/backup.zip": 5000, "/media/video.mp4": 9000})
        root = build_extended_tree(AclAccessService(), user, storage)
        print(f"Запросов к хранилищу после сборки: {len(storage.requests)}")
        client(root)
        print(f"Запросов к хранилищу: {storage.requests}")
        root.print_tree()
        print(f"После повторной печати: {len(storage.requests)} "
              f"(метаданные из кэша)")


if __name__ == "__main__":
    main()
