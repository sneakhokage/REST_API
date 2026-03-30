from fastapi import APIRouter, Depends, HTTPException, Request
from motor.motor_asyncio import AsyncIOMotorDatabase
from pydantic_mongo import PydanticObjectId

from schemas.book import Book, BookCreate
from repository.mongo import get_database
from repository.auth import get_current_user
from middleware.rate_limiter import rate_limit

router = APIRouter(prefix="/api/books", tags=["books"])


async def get_optional_user_id(
    current_user: dict = Depends(get_current_user),
) -> str:
    return current_user["username"]


@router.get("", response_model=list[Book])
async def get_books(
    request: Request,
    limit: int = 10,
    offset: int = 0,
    db: AsyncIOMotorDatabase = Depends(get_database),
    current_user: dict = Depends(get_current_user),
):
    await rate_limit(request, user_id=current_user["username"])
    collection = db["books"]
    cursor = collection.find({})
    books_data = await cursor.skip(offset).limit(limit).to_list(length=limit)
    for item in books_data:
        item["id"] = str(item["_id"])
    return books_data


@router.get("/{book_id}", response_model=Book)
async def get_book(
    request: Request,
    book_id: str,
    db: AsyncIOMotorDatabase = Depends(get_database),
    current_user: dict = Depends(get_current_user),
):
    await rate_limit(request, user_id=current_user["username"])
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