class AppException(Exception):
    """Base application exception."""
    def __init__(self, message: str, status_code: int = 500):
        self.message = message
        self.status_code = status_code
        super().__init__(self.message)


class NotFoundException(AppException):
    """Resource not found exception."""
    def __init__(self, message: str = "Resource not found"):
        super().__init__(message, status_code=404)


class ValidationException(AppException):
    """Validation error exception."""
    def __init__(self, message: str = "Validation error"):
        super().__init__(message, status_code=422)


class DatabaseException(AppException):
    """Database error exception."""
    def __init__(self, message: str = "Database error"):
        super().__init__(message, status_code=500)
