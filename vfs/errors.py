"""Ошибки предметной области."""


class VfsError(Exception):
    """Базовая ошибка виртуальной файловой системы."""


class InvalidTreeOperationError(VfsError):
    """Недопустимая операция над структурой дерева."""


class AccessDeniedError(VfsError):
    """Отказ в доступе.

    Сообщение содержит только пользователя, имя узла и право.
    Размер, содержимое и имена детей закрытого узла не раскрываются.
    """

    def __init__(self, user_name: str, node_name: str, permission) -> None:
        self.user_name = user_name
        self.node_name = node_name
        self.permission = permission
        super().__init__(
            f"Доступ запрещён: у пользователя '{user_name}' "
            f"нет права {permission.name} на '{node_name}'"
        )
