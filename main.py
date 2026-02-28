from __future__ import annotations

from fastapi import FastAPI
from api.books import router as books_router

app = FastAPI(title="Library REST API", version="1.0.0")
app.include_router(books_router)