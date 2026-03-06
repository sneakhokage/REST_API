from __future__ import annotations

from fastapi import FastAPI

from api.books import router as books_router
from repository.database import engine, Base


app = FastAPI(title="Library REST API", version="2.0.0")
app.include_router(books_router)


@app.on_event("startup")
async def on_startup():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)