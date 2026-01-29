from typing import Generic, List, TypeVar

from pydantic import BaseModel

T = TypeVar("T")


class Page(BaseModel, Generic[T]):
    total: int
    items: List[T]
