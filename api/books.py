from __future__ import annotations
import httpx
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Request, Security
from motor.motor_asyncio import AsyncIOMotorDatabase
from pydantic_mongo import PydanticObjectId
from fastapi.security import HTTPAuthorizationCredentials

from schemas.book import Book, BookCreate
from repository.mongo import get_database
from repository.auth import get_current_user, get_optional_current_user, optional_bearer
from middleware.rate_limiter import rate_limit

router = APIRouter(prefix="/api/books", tags=["books"])

@router.get("", response_model=list[Book])
async def get_books(
    request: Request,
    limit: int = 10,
    offset: int = 0,
    db: AsyncIOMotorDatabase = Depends(get_database),
    user: Optional[dict] = Depends(get_optional_current_user),
    _auth: Optional[HTTPAuthorizationCredentials] = Security(optional_bearer)
):
    user_id = user["username"] if user else None
    await rate_limit(request, user_id=user_id)
    collection = db["books"]
    cursor = collection.find({})
    books_data = await cursor.skip(offset).limit(limit).to_list(length=limit)
    for item in books_data:
        item["id"] = str(item["_id"])
    return books_data

@router.get("/external/{external_id}")
async def get_external_book_info(
    request: Request,
    external_id: str,
    user: Optional[dict] = Depends(get_optional_current_user),
    _auth: Optional[HTTPAuthorizationCredentials] = Security(optional_bearer)
):
    user_id = user["username"] if user else None
    await rate_limit(request, user_id=user_id)
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(f"http://prism:4010/books/{external_id}")
            response.raise_for_status()
            return response.json()
        except Exception:
            raise HTTPException(status_code=502, detail="External API error")

@router.get("/{book_id}", response_model=Book)
async def get_book(
    request: Request,
    book_id: str,
    db: AsyncIOMotorDatabase = Depends(get_database),
    user: Optional[dict] = Depends(get_optional_current_user),
    _auth: Optional[HTTPAuthorizationCredentials] = Security(optional_bearer)
):
    user_id = user["username"] if user else None
    await rate_limit(request, user_id=user_id)
    collection = db["books"]
    book = await collection.find_one({"_id": PydanticObjectId(book_id)})
    if not book:
        raise HTTPException(status_code=404, detail="Book not found")
    book["id"] = str(book["_id"])
    return book

@router.post("", response_model=Book)
async def create_book(
    request: Request,
    book: BookCreate,
    db: AsyncIOMotorDatabase = Depends(get_database),
    current_user: dict = Depends(get_current_user),
):
    await rate_limit(request, user_id=current_user["username"])
    collection = db["books"]
    result = await collection.insert_one(book.model_dump())
    new_book = await collection.find_one({"_id": result.inserted_id})
    new_book["id"] = str(new_book["_id"])
    return new_book

@router.put("/{book_id}", response_model=Book)
async def update_book(
    request: Request,
    book_id: str,
    book: BookCreate,
    db: AsyncIOMotorDatabase = Depends(get_database),
    current_user: dict = Depends(get_current_user),
):
    await rate_limit(request, user_id=current_user["username"])
    collection = db["books"]
    update_result = await collection.update_one(
        {"_id": PydanticObjectId(book_id)},
        {"$set": book.model_dump()},
    )
    if update_result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Book not found")
    updated_book = await collection.find_one({"_id": PydanticObjectId(book_id)})
    updated_book["id"] = str(updated_book["_id"])
    return updated_book

@router.delete("/{book_id}")
async def delete_book(
    request: Request,
    book_id: str,
    db: AsyncIOMotorDatabase = Depends(get_database),
    current_user: dict = Depends(get_current_user),
):
    await rate_limit(request, user_id=current_user["username"])
    collection = db["books"]
    response = await collection.delete_one({"_id": PydanticObjectId(book_id)})
    if response.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Book not found")
    return {"message": "Book deleted"}