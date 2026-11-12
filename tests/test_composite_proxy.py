"""Тесты базовой реализации 2.3.2: Composite + ProtectedNodeProxy."""
import unittest

from tests.helpers import RecordingAccess, RecordingNode
from vfs.access import AclAccessService, Permission, User
from vfs.directory import DirectoryComposite
from vfs.errors import AccessDeniedError, InvalidTreeOperationError
from vfs.leaf import FileLeaf
from vfs.protected_proxy import ProtectedNodeProxy

READ, LIST = Permission.READ, Permission.LIST
USER = User("u1", "olesya")


def make_secret():
    secret = DirectoryComposite("secret")
    secret.add(FileLeaf("passwords.txt", 300))
    return secret


class CompositeTest(unittest.TestCase):
    def test_empty_directory(self):
        # пограничный случай
        empty = DirectoryComposite("empty")
        self.assertEqual(empty.size(), 0)
        self.assertEqual(empty.print_tree(), "empty/")
        self.assertIsNone(empty.find("x"))

    def test_nested_size_is_recursive_sum(self):
        # основной сценарий: вложенность и размер
        root, docs, deep = (DirectoryComposite(n) for n in ("root", "docs", "deep"))
        deep.add(FileLeaf("c.txt", 5))
        docs.add(FileLeaf("b.txt", 20))
        docs.add(deep)
        root.add(FileLeaf("a.txt", 100))
        root.add(docs)
        self.assertEqual(root.size(), 125)
        self.assertEqual(
            root.print_tree(),
            "root/\n  a.txt (100 B)\n  docs/\n    b.txt (20 B)\n"
            "    deep/\n      c.txt (5 B)",
        )
        self.assertIs(root.find("c.txt"), deep.children[0])

    def test_remove_child(self):
        root = DirectoryComposite("root")
        leaf = FileLeaf("a.txt", 10)
        root.add(leaf)
        root.remove(leaf)
        self.assertEqual(root.size(), 0)
        with self.assertRaises(InvalidTreeOperationError):
            root.remove(leaf)

    def test_add_directory_into_itself_or_descendant(self):
        # ошибка: каталог в самого себя / в потомка
        a, b = DirectoryComposite("a"), DirectoryComposite("b")
        a.add(b)
        with self.assertRaisesRegex(InvalidTreeOperationError, "в самого себя"):
            a.add(a)
        with self.assertRaises(InvalidTreeOperationError):
            b.add(a)

    def test_cycle_detected_through_proxy(self):
        a = DirectoryComposite("a")
        b = DirectoryComposite("b")
        a.add(ProtectedNodeProxy(b, AclAccessService(), USER))
        with self.assertRaises(InvalidTreeOperationError):
            b.add(a)

    def test_duplicate_name_rejected(self):
        root = DirectoryComposite("root")
        root.add(FileLeaf("a.txt", 1))
        with self.assertRaises(InvalidTreeOperationError):
            root.add(FileLeaf("a.txt", 2))

    def test_leaf_has_no_add(self):
        # вариант «безопасность»: недопустимой операции нет в контракте листа
        self.assertFalse(hasattr(FileLeaf("a.txt", 1), "add"))


class ProtectedProxyTest(unittest.TestCase):
    def setUp(self):
        self.access = AclAccessService()
        self.secret = make_secret()
        self.proxy = ProtectedNodeProxy(self.secret, self.access, USER)
        self.root = DirectoryComposite("root")
        self.root.add(FileLeaf("public.txt", 10))
        self.root.add(self.proxy)

    def test_denied_size_raises_clear_error_without_metadata(self):
        with self.assertRaises(AccessDeniedError) as ctx:
            self.root.size()
        message = str(ctx.exception)
        self.assertIn("olesya", message)
        self.assertIn("READ", message)
        self.assertIn("secret", message)
        self.assertNotIn("300", message)
        self.assertNotIn("passwords", message)

    def test_denied_print_tree_shows_allowed_part_only(self):
        text = self.root.print_tree()
        self.assertEqual(text, "root/\n  public.txt (10 B)\n  secret [нет доступа]")

    def test_denied_find_does_not_reveal_children(self):
        self.assertIsNone(self.root.find("passwords.txt"))

    def test_find_by_own_name_returns_proxy_not_subject(self):
        self.assertIs(self.root.find("secret"), self.proxy)

    def test_allowed_access_delegates_to_subject(self):
        self.access.grant(USER, self.secret, READ, LIST)
        self.assertEqual(self.root.size(), 310)
        self.assertIn("passwords.txt (300 B)", self.root.print_tree())
        self.assertIsNotNone(self.root.find("passwords.txt"))


class InteractionOrderTest(unittest.TestCase):
    """Взаимодействие участников и порядок вызовов.

    Проверка прав выполняется строго до делегирования.
    """

    def make(self, allowed):
        log = []
        node = RecordingNode("n", log)
        proxy = ProtectedNodeProxy(node, RecordingAccess(log, allowed), USER)
        return proxy, log

    def test_size_checks_read_then_delegates(self):
        proxy, log = self.make({READ})
        self.assertEqual(proxy.size(), 42)
        self.assertEqual(log, ["check READ", "subject.size"])

    def test_size_denied_subject_not_called(self):
        proxy, log = self.make(set())
        with self.assertRaises(AccessDeniedError):
            proxy.size()
        self.assertEqual(log, ["check READ"])

    def test_print_tree_checks_list_then_read_then_delegates(self):
        proxy, log = self.make({READ, LIST})
        proxy.print_tree()
        self.assertEqual(log, ["check LIST", "check READ", "subject.print_tree"])

    def test_print_tree_without_list_stops_at_first_check(self):
        proxy, log = self.make({READ})
        self.assertEqual(proxy.print_tree(), "n [нет доступа]")
        self.assertEqual(log, ["check LIST"])

    def test_directory_delegates_to_proxy_child(self):
        log = []
        root = DirectoryComposite("root")
        node = RecordingNode("n", log)
        root.add(ProtectedNodeProxy(node, RecordingAccess(log, {READ}), USER))
        self.assertEqual(root.size(), 42)
        self.assertEqual(log, ["check READ", "subject.size"])


if __name__ == "__main__":
    unittest.main()
