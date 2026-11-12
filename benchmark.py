"""Замер накладных расходов шаблонов.

Запуск: python benchmark.py
1) size() по дереву: вложенные словари без шаблонов, Composite и Composite
   с ProtectedNodeProxy на каждом каталоге (лучшее из 5 запусков);
2) печать дерева с удалёнными файлами: первый вызов загружает метаданные,
   повторный берёт их из кэша (задержка сети имитируется - 2 мс на запрос).
"""
from __future__ import annotations

import sys
import time

from vfs.access import AclAccessService, Permission, User
from vfs.directory import DirectoryComposite
from vfs.leaf import FileLeaf
from vfs.protected_proxy import ProtectedNodeProxy
from vfs.remote import InMemoryRemoteStorage, LazyRemoteFileProxy, RemoteMetadata

READ, LIST = Permission.READ, Permission.LIST
USER = User("u1", "olesya")


def build_tree(dirs: int, files: int, proxied: bool) -> DirectoryComposite:
    access = AclAccessService()
    root = DirectoryComposite("root")
    for i in range(dirs):
        directory = DirectoryComposite(f"d{i}")
        for j in range(files):
            directory.add(FileLeaf(f"f{j}", 1))
        if proxied:
            access.grant(USER, directory, READ, LIST)
            root.add(ProtectedNodeProxy(directory, access, USER))
        else:
            root.add(directory)
    return root


def build_dict(dirs: int, files: int) -> dict:
    # Решение без шаблонов: дерево из словарей, тип узла проверяется вручную.
    return {f"d{i}": {f"f{j}": 1 for j in range(files)} for i in range(dirs)}


def dict_size(tree: dict) -> int:
    return sum(dict_size(v) if isinstance(v, dict) else v for v in tree.values())


def best_ms(fn, repeat: int = 5) -> float:
    times = []
    for _ in range(repeat):
        start = time.perf_counter()
        fn()
        times.append(time.perf_counter() - start)
    return min(times) * 1000


class SlowStorage(InMemoryRemoteStorage):
    def fetch_metadata(self, path: str) -> RemoteMetadata:
        time.sleep(0.002)  # имитация сетевой задержки
        return super().fetch_metadata(path)


def main() -> None:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")

    print("size(): время, мс (лучшее из 5)")
    print(f"{'узлов':>8} {'словари':>9} {'Composite':>10} {'+Proxy':>8} {'Proxy/Comp':>11}")
    for dirs, files in ((10, 100), (100, 100), (1000, 100)):
        nodes = dirs * (files + 1) + 1
        raw = build_dict(dirs, files)
        plain = build_tree(dirs, files, proxied=False)
        proxied = build_tree(dirs, files, proxied=True)
        t_raw = best_ms(lambda: dict_size(raw))
        t_plain = best_ms(plain.size)
        t_proxy = best_ms(proxied.size)
        print(f"{nodes:>8} {t_raw:>9.2f} {t_plain:>10.2f} {t_proxy:>8.2f} "
              f"{t_proxy / t_plain:>11.2f}")

    print("\nУдалённые файлы: 50 шт., задержка 2 мс на запрос")
    files = {f"/cloud/file{i}.bin": 1000 + i for i in range(50)}
    storage = SlowStorage(files)
    access = AclAccessService()
    cloud = DirectoryComposite("cloud")
    for path in files:
        remote = LazyRemoteFileProxy(path.rsplit("/", 1)[1], storage, path)
        access.grant(USER, remote, READ, LIST)
        cloud.add(ProtectedNodeProxy(remote, access, USER))
    for label in ("первая печать", "повторная печать"):
        before = len(storage.requests)
        start = time.perf_counter()
        cloud.print_tree()
        elapsed = (time.perf_counter() - start) * 1000
        print(f"{label}: {elapsed:.1f} мс, запросов {len(storage.requests) - before}")


if __name__ == "__main__":
    main()
