from __future__ import annotations
import uuid


class BookRepository:
    def __init__(self, database: list[dict]):
        self.db = database

    async def get_all(self) -> list[dict]:
        return self.db

    async def get_by_id(self, book_id: uuid.UUID) -> dict | None:
        for item in self.db:
            if item["id"] == book_id:
                return item
        return None

    async def create(self, book_dict: dict) -> dict:
        self.db.append(book_dict)
        return book_dict

    async def delete(self, book_id: uuid.UUID) -> bool:
        for idx, item in enumerate(self.db):
            if item["id"] == book_id:
                self.db.pop(idx)
                return True
        return False