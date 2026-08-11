from typing import Generic, TypeVar

from pydantic import BaseModel

T = TypeVar("T")


class ApiResponse(BaseModel, Generic[T]):
    status: str
    result: T


SUCCESS = "success"
ERROR = "error"


def ok(result: T) -> ApiResponse[T]:
    return ApiResponse(status=SUCCESS, result=result)


def fail(result: T) -> ApiResponse[T]:
    return ApiResponse(status=ERROR, result=result)