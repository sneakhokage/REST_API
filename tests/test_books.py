from httpx import AsyncClient, ASGITransport
import pytest
from main import app

# Валідний ObjectID для тесту 404 (24 символи)
NOT_FOUND_ID = "507f1f77bcf86cd799439011"


@pytest.fixture
def transport():
    return ASGITransport(app=app)


@pytest.mark.asyncio
async def test_create_book(transport):
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        response = await ac.post("/api/books", json={
            "title": "Test Book",
            "author": "Author",
            "description": "Test description",
            "status": "available",
            "year": 2026
        })
    assert response.status_code == 200
    data = response.json()
    assert data["title"] == "Test Book"
    assert "id" in data


@pytest.mark.asyncio
async def test_get_books(transport):
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        response = await ac.get("/api/books")
    assert response.status_code == 200
    assert isinstance(response.json(), list)


@pytest.mark.asyncio
async def test_get_book_by_id(transport):
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        # Створюємо книгу, щоб точно знати ID
        create = await ac.post("/api/books", json={
            "title": "Unique Book",
            "author": "Unique Author",
            "description": "Desc",
            "status": "available",
            "year": 2026
        })
        book_id = create.json()["id"]

        response = await ac.get(f"/api/books/{book_id}")
    assert response.status_code == 200
    assert response.json()["id"] == book_id


@pytest.mark.asyncio
async def test_update_book(transport):
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        # Створюємо книгу
        create = await ac.post("/api/books", json={
            "title": "Old Title",
            "author": "Author",
            "description": "Old desc",
            "status": "available",
            "year": 2020
        })
        book_id = create.json()["id"]

        # Оновлюємо її
        response = await ac.put(f"/api/books/{book_id}", json={
            "title": "New Title",
            "author": "Author",
            "description": "New desc",
            "status": "borrowed",
            "year": 2026
        })
    assert response.status_code == 200
    assert response.json()["title"] == "New Title"


@pytest.mark.asyncio
async def test_delete_book(transport):
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        # Створюємо книгу
        create = await ac.post("/api/books", json={
            "title": "To Delete",
            "author": "Author",
            "description": "Desc",
            "status": "available",
            "year": 2022
        })
        book_id = create.json()["id"]

        # Видаляємо
        response = await ac.delete(f"/api/books/{book_id}")
    assert response.status_code == 200


@pytest.mark.asyncio
async def test_book_not_found(transport):
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        response = await ac.get(f"/api/books/{NOT_FOUND_ID}")
    assert response.status_code == 404