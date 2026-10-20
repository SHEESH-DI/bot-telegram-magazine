class CatalogError(Exception):
    """Ожидаемая ошибка при работе с каталогом."""


class NotFound(CatalogError):
    pass


class Conflict(CatalogError):
    pass


class InvalidInput(CatalogError):
    pass


class StorageUnavailable(CatalogError):
    pass
