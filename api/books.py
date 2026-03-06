from __future__ import annotations

import uuid
from typing import Literal

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from repository.database import get_session
from repository.book_repository import BookRepository
from schemas.book import BookCreateRequest, BookResponse, BookListResponse, BookStatus
from services.book_service import BookService

router = APIRouter(prefix="/api", tags=["Books"])


@router.get("/health", status_code=status.HTTP_200_OK)
async def health():
    return {"status": "ok"}


@router.get("/books", response_model=BookListResponse, status_code=status.HTTP_200_OK)
async def get_all_books(
    status_filter: BookStatus | None = Query(default=None, alias="status"),
    author: str | None = Query(default=None),
    sort_by: Literal["title", "year"] | None = Query(default=None),
    order: Literal["asc", "desc"] = Query(default="asc"),
    limit: int = Query(default=10, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    session: AsyncSession = Depends(get_session),
):
    service = BookService(BookRepository(session))
    items, total = await service.get_all(
        status=status_filter.value if status_filter else None,
        author=author,
        sort_by=sort_by,
        order=order,
        limit=limit,
        offset=offset,
    )

    return {
        "items": items,
        "total": total,
        "limit": limit,
        "offset": offset,
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