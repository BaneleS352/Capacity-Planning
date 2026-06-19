from fastapi import Query
from pydantic import BaseModel, Field

from app.core.config import get_settings


class Page[T](BaseModel):
    items: list[T]
    total: int = Field(ge=0)
    page: int = Field(ge=1)
    page_size: int = Field(ge=1)
    pages: int = Field(ge=0)


class Pagination:
    def __init__(
        self,
        page: int = Query(1, ge=1),
        page_size: int = Query(get_settings().default_page_size, ge=1),
    ) -> None:
        self.page = page
        self.page_size = min(page_size, get_settings().max_page_size)

    @property
    def offset(self) -> int:
        return (self.page - 1) * self.page_size


def make_page[T](items: list[T], total: int, pagination: Pagination) -> Page[T]:
    pages = (total + pagination.page_size - 1) // pagination.page_size if total else 0
    return Page(
        items=items,
        total=total,
        page=pagination.page,
        page_size=pagination.page_size,
        pages=pages,
    )
