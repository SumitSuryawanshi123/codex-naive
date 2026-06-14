class AppError(Exception):
    """Base class for expected application errors."""


class NotFoundError(AppError):
    pass


class ValidationError(AppError):
    pass
