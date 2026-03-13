from fastapi import FastAPI
from api.books import router as books_router

app = FastAPI(title="REST_API")

@app.get("/api/health")
async def health():
    return {"status": "ok"}

app.include_router(books_router)