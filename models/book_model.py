from __future__ import annotations
import uuid

db: list[dict] = [
    {
        "id": uuid.uuid4(),
        "title": "Test",
        "author": "NAME",
        "description": "Demo book",
        "status": "available",
        "year": 2020,
    }
]