from __future__ import annotations

import uuid
from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field, ConfigDict, field_validator


class BookStatus(str, Enum):
    available = "available"
    issued = "issued"


class BookCreateRequest(BaseModel):
    title: str = Field(min_length=2, max_length=200)
    author: str = Field(min_length=2, max_length=120)
    description: Optional[str] = Field(default=None, max_length=2000)
    status: BookStatus = Field(default=BookStatus.available)
    year: int = Field(ge=1400, le=2100)

    @field_validator("title")
    @classmethod
    def title_not_start_with_underscore(cls, value: str) -> str:
        if value.startswith("_"):
            raise ValueError("Title must not start with underscore")
        return value


class BookResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    title: str
    author: str
    description: Optional[str]
    status: BookStatus
    year: int


class BookListCursorResponse(BaseModel):
    items: list[BookResponse]
    next_cursor: Optional[str] = None
    limit: int