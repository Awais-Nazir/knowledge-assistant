from typing import Any, TypeVar

from pydantic import BaseModel

T = TypeVar("T")


class ErrorResponse(BaseModel):
    error: bool = True
    error_code: str
    message: str
    details: Any = None


class SuccessResponse(BaseModel):
    success: bool = True
    message: str


class PaginatedResponse[T](BaseModel):
    items: list[T]
    total: int
    page: int
    page_size: int
    has_next: bool
    has_previous: bool
