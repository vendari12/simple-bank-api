from http import HTTPStatus
from typing import Any, Dict, Optional

from fastapi.exceptions import HTTPException


class DBConfigError(Exception):
    """Raised when the requested database configuration is not present.

    This custom exception is used to indicate that a specific
    database configuration cannot be found or is not available.

    Attributes:
        message (str): Optional message providing additional context about the error.
    """

    def __init__(
        self, message: Optional[str] = "Database configuration not found"
    ) -> None:
        super().__init__(message)


class DuplicatedEntryError(HTTPException):
    """Exception raised for duplicated entries in the database.

    This exception corresponds to HTTP 409 Conflict status and is
    typically raised when attempting to create or insert a record
    that violates a unique constraint (e.g., duplicate key).

    Args:
        detail (str): additional information about the error.
        headers (Dict[str, str] | None): Optional headers to include in the response.
    """

    def __init__(self, detail: str, headers: Dict[str, str] | None = None) -> None:
        super().__init__(HTTPStatus.CONFLICT, detail, headers)


class ServerHTTPException(HTTPException):
    """Exception raised for server-side errors.

    This exception corresponds to HTTP 500 Internal Server Error status.
    It's used to indicate that an unexpected server error has occurred.

    Args:
        error (str):  error message describing the server issue.
    """

    def __init__(self, error: str) -> None:
        super(ServerHTTPException, self).__init__(
            status_code=HTTPStatus.INTERNAL_SERVER_ERROR, detail=error
        )


class ObjectNotFound(HTTPException):
    """Exception raised when a requested object is not found.

    This exception corresponds to HTTP 404 Not Found status.
    It's used to indicate that a specific resource or object could not be located.

    Args:
        message (str): The error message providing details about the missing object.
    """

    def __init__(self, message: str) -> None:
        super().__init__(status_code=HTTPStatus.NOT_FOUND, detail=message)


class BadRequest(HTTPException):
    """Exception raised for invalid or bad requests.

    This exception corresponds to HTTP 400 Bad Request status.
    It's used to indicate that the request sent by the client is invalid or malformed.

    Args:
        reason (str): The error message explaining why the request is invalid.
    """

    def __init__(self, reason: str) -> None:
        super().__init__(status_code=HTTPStatus.BAD_REQUEST, detail=reason)


class ConfigurationError(HTTPException):
    """Exception raised for configuration-related errors.

    This exception corresponds to HTTP 500 Internal Server Error status.
    It's used to indicate that a critical configuration error has occurred on the server.

    Args:
        error (str): error message describing the configuration issue.
    """

    def __init__(self, error: str) -> None:
        super(ConfigurationError, self).__init__(
            status_code=HTTPStatus.INTERNAL_SERVER_ERROR, detail=error
        )
