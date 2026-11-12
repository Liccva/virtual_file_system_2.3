# Вариант 2.3. Виртуальная файловая система (Composite + Proxy)

Единое дерево локальных файлов, каталогов и удалённых объектов с проверкой прав,
ленивой загрузкой и кэшем метаданных. Python 3.10+, без внешних зависимостей.

## Запуск

```
python main.py                 # демонстрация до и после расширения
python -m unittest -v          # 32 теста
```

## Структура

| Файл | Содержание |
|---|---|
| `vfs/node.py` | `FileSystemNode` — общий контракт (Component / Subject) |
| `vfs/leaf.py` | `FileLeaf` — файл (Leaf) |
| `vfs/directory.py` | `DirectoryComposite` — каталог (Composite) |
| `vfs/access.py` | `Permission`, `User`, `AccessService`, `AclAccessService` — сервис прав |
| `vfs/protected_proxy.py` | `ProtectedNodeProxy` — защищающий заместитель |
| `vfs/errors.py` | `AccessDeniedError`, `InvalidTreeOperationError` |
| `vfs/symlink.py` | расширение: `SymbolicLink` с контролем циклов |
| `vfs/remote.py` | расширение: `LazyRemoteFileProxy`, `RemoteStorage` |
| `main.py` | точка сборки (composition root) и клиентский сценарий |
| `tests/` | тесты базовой части, расширения и архитектурные проверки |
| `docs/uml/` | диаграммы классов (`diagrams_gen.py`) и последовательности (`seq_*.puml`) |
