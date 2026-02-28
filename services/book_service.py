from __future__ import annotations

import uuid
from typing import Optional

from schemas.book import BookCreateRequest, BookStatus


class BookService:
    def __init__(self, repository):
        self.repository = repository

    async def get_all(
        self,
        status: Optional[BookStatus] = None,
        author: Optional[str] = None,
        sort_by: Optional[str] = None,
        order: str = "asc",
    ) -> list[dict]:
        items = list(await self.repository.get_all())

        if status is not None:
            items = [x for x in items if x.get("status") == status.value]

        if author is not None:
            a = author.strip().lower()
            items = [x for x in items if x.get("author", "").strip().lower() == a]

        reverse = order.lower().strip() == "desc"
        if sort_by == "title":
            items.sort(key=lambda x: x.get("title", "").lower(), reverse=reverse)
        elif sort_by == "year":
            items.sort(key=lambda x: x.get("year", 0), reverse=reverse)

        return items

    async def get_by_id(self, book_id: uuid.UUID) -> dict | None:
        return await self.repository.get_by_id(book_id)

    async def create(self, book: BookCreateRequest) -> dict:
        book_dict = {
            "id": uuid.uuid4(),
            "title": book.title,
            "author": book.author,
            "description": book.description,
            "status": book.status.value,
            "year": book.year,
        }
        return await self.repository.create(book_dict)

    async def delete_idempotent(self, book_id: uuid.UUID) -> None:

        await self.repository.delete(book_id)