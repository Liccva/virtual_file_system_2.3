"""Тесты расширения 2.3.3: SymbolicLink и LazyRemoteFileProxy."""
import contextlib
import io
import sys
import unittest

import main
from vfs.access import AclAccessService, Permission, User
from vfs.directory import DirectoryComposite
from vfs.errors import AccessDeniedError
from vfs.leaf import FileLeaf
from vfs.protected_proxy import ProtectedNodeProxy
from vfs.remote import (InMemoryRemoteStorage, LazyRemoteFileProxy,
                        RemoteStorageError)
from vfs.symlink import SymbolicLink

READ, LIST = Permission.READ, Permission.LIST
USER = User("u1", "olesya")
PATH = "/backups/backup.zip"


class LazyRemoteTest(unittest.TestCase):
    def setUp(self):
        self.storage = InMemoryRemoteStorage({PATH: 5000})
        self.access = AclAccessService()
        self.remote = LazyRemoteFileProxy("backup.zip", self.storage, PATH)
        self.node = ProtectedNodeProxy(self.remote, self.access, USER)

    def test_nothing_loaded_on_creation(self):
        self.assertFalse(self.remote.is_loaded)
        self.assertEqual(self.storage.requests, [])

    def test_no_load_when_access_denied(self):
        with self.assertRaises(AccessDeniedError):
            self.node.size()
        self.assertEqual(self.node.print_tree(), "backup.zip [нет доступа]")
        self.assertEqual(self.storage.requests, [])
        self.assertFalse(self.remote.is_loaded)

    def test_loads_on_first_allowed_access_and_caches_metadata(self):
        self.access.grant(USER, self.remote, READ, LIST)
        self.assertEqual(self.node.size(), 5000)
        self.assertEqual(self.node.size(), 5000)
        self.assertEqual(self.node.print_tree(), "backup.zip (5000 B) [remote]")
        self.assertEqual(self.storage.requests, [PATH])

    def test_find_by_name_does_not_load(self):
        self.assertIs(self.remote.find("backup.zip"), self.remote)
        self.assertEqual(self.storage.requests, [])

    def test_load_error_is_not_cached(self):
        storage = InMemoryRemoteStorage()
        remote = LazyRemoteFileProxy("x.bin", storage, "/x.bin")
        with self.assertRaises(RemoteStorageError):
            remote.size()
        storage.put("/x.bin", 7)
        self.assertEqual(remote.size(), 7)
        self.assertEqual(len(storage.requests), 2)


class SymbolicLinkTest(unittest.TestCase):
    def setUp(self):
        self.root = DirectoryComposite("root")
        self.docs = DirectoryComposite("docs")
        self.docs.add(FileLeaf("a.txt", 10))
        self.root.add(self.docs)

    def test_link_follows_target_in_print_and_find(self):
        self.root.add(SymbolicLink("shortcut", self.docs))
        expected = "shortcut -> docs\n    docs/\n      a.txt (10 B)"
        self.assertIn(expected, self.root.print_tree())
        self.assertIs(self.root.find("shortcut").target, self.docs)

    def test_link_size_not_double_counted(self):
        self.root.add(SymbolicLink("shortcut", self.docs))
        self.assertEqual(self.root.size(), 10)

    def test_cycle_of_links_is_detected(self):
        self.docs.add(SymbolicLink("loop", self.docs))
        text = self.root.print_tree()
        self.assertIn("loop -> docs [цикл, не раскрывается]", text)
        self.assertIsNone(self.root.find("missing"))

    def test_cycle_to_ancestor(self):
        self.docs.add(SymbolicLink("up", self.root))
        self.assertEqual(self.root.print_tree().count("[цикл, не раскрывается]"), 1)
        self.assertIsNone(self.root.find("missing"))

    def test_link_to_protected_node_keeps_access_check(self):
        secret = DirectoryComposite("secret")
        secret.add(FileLeaf("passwords.txt", 300))
        proxy = ProtectedNodeProxy(secret, AclAccessService(), USER)
        self.root.add(SymbolicLink("secret_link", proxy))
        expected = "secret_link -> secret\n    secret [нет доступа]"
        self.assertIn(expected, self.root.print_tree())
        self.assertIsNone(self.root.find("passwords.txt"))

    def test_link_does_not_own_target(self):
        # ссылка на предка не мешает обычным операциям над структурой
        link = SymbolicLink("up", self.root)
        self.docs.add(link)
        self.docs.add(DirectoryComposite("new"))
        self.assertFalse(link.contains(self.root))


class DepthTest(unittest.TestCase):
    def test_deep_nesting_within_recursion_limit(self):
        root = current = DirectoryComposite("d0")
        for i in range(1, 200):
            nxt = DirectoryComposite(f"d{i}")
            current.add(nxt)
            current = nxt
        current.add(FileLeaf("leaf", 1))
        self.assertEqual(root.size(), 1)
        self.assertIsNotNone(root.find("leaf"))


class ClientScenarioTest(unittest.TestCase):
    def test_same_client_works_before_and_after_extension(self):
        out = io.StringIO()
        with contextlib.redirect_stdout(out):
            main.client(main.build_base_tree(AclAccessService(), main.OLESYA))
            storage = InMemoryRemoteStorage({PATH: 5000, "/media/video.mp4": 9000})
            access = AclAccessService()
            main.client(main.build_extended_tree(access, main.OLESYA, storage))
        text = out.getvalue()
        self.assertEqual(text.count("secret [нет доступа]"), 3)
        self.assertIn("video.mp4 [нет доступа]", text)
        self.assertEqual(storage.requests, [PATH])


if __name__ == "__main__":
    unittest.main()
