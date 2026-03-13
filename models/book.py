from pydantic import BaseModel
from pydantic_mongo import PydanticObjectId

class Book(BaseModel):
    id: PydanticObjectId | None = None
    title: str
    author: str
    description: str | None = None
    status: str
    year: int