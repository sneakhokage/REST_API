from pydantic import BaseModel, ConfigDict


class BookCreate(BaseModel):
    title: str
    author: str
    description: str
    status: str
    year: int

class Book(BookCreate):
    id: str

model_config = ConfigDict(populate_by_name=True, arbitrary_types_allowed=True)