"""Архитектурные проверки по исходному тексту пакета vfs."""
import ast
import pathlib
import unittest

VFS = pathlib.Path(__file__).resolve().parent.parent / "vfs"
BASE = ["node.py", "leaf.py", "directory.py", "access.py", "protected_proxy.py", "errors.py"]
EXTENSION = {"symlink", "remote"}


def parse(path):
    return ast.parse(path.read_text(encoding="utf-8"))


def imported_modules(path):
    names = set()
    for node in ast.walk(parse(path)):
        if isinstance(node, ast.ImportFrom) and node.module:
            names.add(node.module.split(".")[-1])
        elif isinstance(node, ast.Import):
            names.update(alias.name.split(".")[-1] for alias in node.names)
    return names


class ArchitectureTest(unittest.TestCase):
    def test_base_modules_do_not_depend_on_extension(self):
        # Расширение зависит от базовых модулей, но не наоборот:
        # значит, при его добавлении базовые модули менять не требовалось.
        for name in BASE:
            with self.subTest(module=name):
                self.assertEqual(imported_modules(VFS / name) & EXTENSION, set())

    def test_no_type_checks_instead_of_polymorphism(self):
        # В пакете нет isinstance/issubclass и match: поведение выбирает полиморфизм.
        offenders = []
        for path in sorted(VFS.glob("*.py")):
            for node in ast.walk(parse(path)):
                if isinstance(node, ast.Match):
                    offenders.append(f"{path.name}: match")
                if (isinstance(node, ast.Call) and isinstance(node.func, ast.Name)
                        and node.func.id in {"isinstance", "issubclass"}):
                    offenders.append(f"{path.name}:{node.lineno} {node.func.id}")
        self.assertEqual(offenders, [])


if __name__ == "__main__":
    unittest.main()
