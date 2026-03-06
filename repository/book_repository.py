from __future__ import annotations

import uuid

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from models.book_model import Book


class BookRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_all(
        self,
        status: str | None = None,
        author: str | None = None,
        sort_by: str | None = None,
        order: str = "asc",
        limit: int = 10,
        offset: int = 0,
    ) -> tuple[list[Book], int]:
        stmt = select(Book)

        count_stmt = select(func.count()).select_from(Book)

        if status:
            stmt = stmt.where(Book.status == status)
            count_stmt = count_stmt.where(Book.status == status)

        if author:
            stmt = stmt.where(Book.author == author)
            count_stmt = count_stmt.where(Book.author == author)

        if sort_by == "title":
            stmt = stmt.order_by(Book.title.desc() if order == "desc" else Book.title.asc())
        elif sort_by == "year":
            stmt = stmt.order_by(Book.year.desc() if order == "desc" else Book.year.asc())

        stmt = stmt.limit(limit).offset(offset)

        result = await self.session.execute(stmt)
        books = result.scalars().all()

        total_result = await self.session.execute(count_stmt)
        total = total_result.scalar_one()

        return books, total

    async def get_by_id(self, book_id: uuid.UUID) -> Book | None:
        stmt = select(Book).where(Book.id == book_id)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def create(self, book: Book) -> Book:
        self.session.add(book)
        await self.session.commit()
        await self.session.refresh(book)
        return book

    async def delete(self, book_id: uuid.UUID) -> bool:
        book = await self.get_by_id(book_id)
        if book is None:
            return False

        await self.session.delete(book)
        await self.session.commit()
        return True