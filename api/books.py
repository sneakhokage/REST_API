from __future__ import annotations

import uuid
from typing import Optional, Literal

from fastapi import APIRouter, HTTPException, Query, status

from models.book_model import db
from repository.book_repository import BookRepository
from schemas.book import BookCreateRequest, BookResponse, BookStatus
from services.book_service import BookService

router = APIRouter(prefix="/api", tags=["Books"])

repo = BookRepository(db)
service = BookService(repo)


@router.get("/health", status_code=status.HTTP_200_OK)
async def health():
    return {"status": "ok"}


@router.get("/books", response_model=list[BookResponse], status_code=status.HTTP_200_OK)
async def get_all_books(
    status_filter: Optional[BookStatus] = Query(default=None, alias="status"),
    author: Optional[str] = Query(default=None),
    sort_by: Optional[Literal["title", "year"]] = Query(default=None),
    order: Literal["asc", "desc"] = Query(default="asc"),
):
    return await service.get_all(status=status_filter, author=author, sort_by=sort_by, order=order)


@router.get("/books/{book_id}", response_model=BookResponse, status_code=status.HTTP_200_OK)
async def get_book_by_id(book_id: uuid.UUID):
    item = await service.get_by_id(book_id)
    if item is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Book not found")
    return item


@router.post("/books", response_model=BookResponse, status_code=status.HTTP_201_CREATED)
async def create_book(book: BookCreateRequest):
    return await service.create(book)


@router.delete("/books/{book_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_book(book_id: uuid.UUID):
    await service.delete_idempotent(book_id)
    return