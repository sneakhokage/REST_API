from __future__ import annotations

import uuid
from typing import Literal

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from repository.database import get_session
from repository.book_repository import BookRepository
from schemas.book import (
    BookCreateRequest,
    BookResponse,
    BookListCursorResponse,
    BookStatus,
)
from services.book_service import BookService

router = APIRouter(prefix="/api", tags=["Books"])


@router.get("/health", status_code=status.HTTP_200_OK)
async def health():
    return {"status": "ok"}


@router.get("/books", response_model=BookListCursorResponse, status_code=status.HTTP_200_OK)
async def get_all_books(
    status_filter: BookStatus | None = Query(default=None, alias="status"),
    author: str | None = Query(default=None),
    sort_by: Literal["title", "year"] | None = Query(default="year"),
    order: Literal["asc", "desc"] = Query(default="asc"),
    limit: int = Query(default=10, ge=1, le=100),
    cursor: str | None = Query(default=None),
    session: AsyncSession = Depends(get_session),
):
    service = BookService(BookRepository(session))
    books = await service.get_all(
        status=status_filter.value if status_filter else None,
        author=author,
        sort_by=sort_by,
        order=order,
        limit=limit,
        cursor=cursor,
    )

    has_next = len(books) > limit
    items = books[:limit]

    next_cursor = None
    if has_next and items:
        last_item = items[-1]

        if sort_by == "title":
            next_cursor = f"{last_item.title}|{last_item.id}"
        else:
            next_cursor = f"{last_item.year}|{last_item.id}"

    return {
        "items": items,
        "next_cursor": next_cursor,
        "limit": limit,
    }


@router.get("/books/{book_id}", response_model=BookResponse, status_code=status.HTTP_200_OK)
async def get_book_by_id(
    book_id: uuid.UUID,
    session: AsyncSession = Depends(get_session),
):
    service = BookService(BookRepository(session))
    book = await service.get_by_id(book_id)

    if book is None:
        raise HTTPException(status_code=404, detail="Book not found")

    return book


@router.post("/books", response_model=BookResponse, status_code=status.HTTP_201_CREATED)
async def create_book(
    data: BookCreateRequest,
    session: AsyncSession = Depends(get_session),
):
    service = BookService(BookRepository(session))
    return await service.create(data)


@router.delete("/books/{book_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_book(
    book_id: uuid.UUID,
    session: AsyncSession = Depends(get_session),
):
    service = BookService(BookRepository(session))
    await service.delete_idempotent(book_id)
    return