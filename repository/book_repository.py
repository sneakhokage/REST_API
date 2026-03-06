from __future__ import annotations

import uuid
from sqlalchemy import select, and_, or_
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
        cursor: str | None = None,
    ) -> list[Book]:
        stmt = select(Book)

        if status:
            stmt = stmt.where(Book.status == status)

        if author:
            stmt = stmt.where(Book.author == author)

        if sort_by not in ("title", "year", None):
            sort_by = None

        if sort_by == "title":
            if order == "desc":
                stmt = stmt.order_by(Book.title.desc(), Book.id.desc())
            else:
                stmt = stmt.order_by(Book.title.asc(), Book.id.asc())

            if cursor:
                cursor_title, cursor_id = cursor.split("|")
                cursor_uuid = uuid.UUID(cursor_id)

                if order == "desc":
                    stmt = stmt.where(
                        or_(
                            Book.title < cursor_title,
                            and_(Book.title == cursor_title, Book.id < cursor_uuid),
                        )
                    )
                else:
                    stmt = stmt.where(
                        or_(
                            Book.title > cursor_title,
                            and_(Book.title == cursor_title, Book.id > cursor_uuid),
                        )
                    )

        else:
            if order == "desc":
                stmt = stmt.order_by(Book.year.desc(), Book.id.desc())
            else:
                stmt = stmt.order_by(Book.year.asc(), Book.id.asc())

            if cursor:
                cursor_year, cursor_id = cursor.split("|")
                cursor_year = int(cursor_year)
                cursor_uuid = uuid.UUID(cursor_id)

                if order == "desc":
                    stmt = stmt.where(
                        or_(
                            Book.year < cursor_year,
                            and_(Book.year == cursor_year, Book.id < cursor_uuid),
                        )
                    )
                else:
                    stmt = stmt.where(
                        or_(
                            Book.year > cursor_year,
                            and_(Book.year == cursor_year, Book.id > cursor_uuid),
                        )
                    )

        stmt = stmt.limit(limit + 1)

        result = await self.session.execute(stmt)
        books = result.scalars().all()
        return books

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