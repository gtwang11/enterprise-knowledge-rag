"""统一响应模型"""

from typing import Optional, List, TypeVar, Generic
from pydantic import BaseModel

T = TypeVar("T")


class ApiResponse(BaseModel, Generic[T]):
    code: int = 200
    message: str = "success"
    data: Optional[T] = None
    timestamp: int = 0


class PageData(BaseModel, Generic[T]):
    items: List[T]
    total: int
    page: int
    page_size: int
    total_pages: int


class PageResponse(BaseModel, Generic[T]):
    code: int = 200
    message: str = "success"
    data: Optional[PageData[T]] = None
    timestamp: int = 0
