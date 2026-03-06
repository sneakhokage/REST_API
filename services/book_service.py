from __future__ import annotations

import uuid

from models.book_model import Book
from repository.book_repository import BookRepository
from schemas.book import BookCreateRequest


class BookService:
    def __init__(self, repository: BookRepository):
        self.repository = repository

    async def get_all(
        self,
        status: str | None,
        author: str | None,
        sort_by: str | None,
        order: str,
        limit: int,
        cursor: str | None,
    ):
        return await self.repository.get_all(
            status=status,
            author=author,
            sort_by=sort_by,
            order=order,
            limit=limit,
            cursor=cursor,
        )

    async def get_by_id(self, book_id: uuid.UUID):
        return await self.repository.get_by_id(book_id)

    async def create(self, data: BookCreateRequest):
        book = Book(
            title=data.title,
            author=data.author,
            description=data.description,
            status=data.status.value,
            year=data.year,
        )
        return await self.repository.create(book)

    async def delete_idempotent(self, book_id: uuid.UUID) -> None:
        await self.repository.delete(book_id)