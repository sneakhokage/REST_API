from __future__ import annotations

import uuid
from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field, field_validator


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
    def title_not_start_with_underscore(cls, v: str) -> str:
        if v.startswith("_"):
            raise ValueError("Title must not start with underscore")
        return v


class BookResponse(BaseModel):
    id: uuid.UUID
    title: str
    author: str
    description: Optional[str] = None
    status: BookStatus
    year: int