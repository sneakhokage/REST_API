from httpx import AsyncClient, ASGITransport
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from bson import ObjectId
from main import app

NOT_FOUND_ID = "507f1f77bcf86cd799439011"

FAKE_USER = {
    "_id": ObjectId(),
    "username": "testuser",
    "hashed_password": "$2b$12$test"
}

FAKE_BOOK = {
    "_id": ObjectId("507f1f77bcf86cd799439012"),
    "id": "507f1f77bcf86cd799439012",
    "title": "Test Book",
    "author": "Author",
    "description": "Test description",
    "status": "available",
    "year": 2026
}


def make_mock_db(user=FAKE_USER, book=FAKE_BOOK, book_found=True):
    mock_db = MagicMock()

    users_col = MagicMock()
    users_col.find_one = AsyncMock(return_value=user)
    users_col.insert_one = AsyncMock(return_value=MagicMock(inserted_id=ObjectId()))

    books_col = MagicMock()
    books_col.find_one = AsyncMock(return_value=book if book_found else None)
    books_col.insert_one = AsyncMock(return_value=MagicMock(inserted_id=book["_id"]))
    books_col.update_one = AsyncMock(return_value=MagicMock(matched_count=1 if book_found else 0))
    books_col.delete_one = AsyncMock(return_value=MagicMock(deleted_count=1 if book_found else 0))

    cursor = MagicMock()
    cursor.skip = MagicMock(return_value=cursor)
    cursor.limit = MagicMock(return_value=cursor)
    cursor.to_list = AsyncMock(return_value=[book])
    books_col.find = MagicMock(return_value=cursor)

    def get_col(name):
        if name == "users":
            return users_col
        return books_col

    mock_db.__getitem__ = MagicMock(side_effect=get_col)
    return mock_db


def get_token():
    from repository.auth import create_access_token
    return create_access_token({"sub": "testuser"})


@pytest.fixture
def transport():
    return ASGITransport(app=app)


@pytest.mark.asyncio
async def test_register(transport):
    mock_db = make_mock_db(user=None)
    mock_db["users"].find_one = AsyncMock(return_value=None)

    from repository.mongo import get_database
    app.dependency_overrides[get_database] = lambda: mock_db

    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        response = await ac.post("/api/auth/register", json={
            "username": "newuser",
            "password": "newpass"
        })
    app.dependency_overrides.clear()
    assert response.status_code == 201


@pytest.mark.asyncio
async def test_login(transport):
    import bcrypt
    hashed = bcrypt.hashpw("testpass".encode(), bcrypt.gensalt()).decode()
    user = {**FAKE_USER, "hashed_password": hashed}
    mock_db = make_mock_db(user=user)

    from repository.mongo import get_database
    app.dependency_overrides[get_database] = lambda: mock_db

    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        response = await ac.post("/api/auth/login", json={
            "username": "testuser",
            "password": "testpass"
        })
    app.dependency_overrides.clear()
    assert response.status_code == 200
    assert "access_token" in response.json()
    assert "refresh_token" in response.json()


@pytest.mark.asyncio
async def test_refresh_token(transport):
    from repository.auth import create_refresh_token
    from repository.mongo import get_database
    mock_db = make_mock_db()
    app.dependency_overrides[get_database] = lambda: mock_db

    refresh_token = create_refresh_token({"sub": "testuser"})
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        response = await ac.post("/api/auth/refresh", json={
            "refresh_token": refresh_token
        })
    app.dependency_overrides.clear()
    assert response.status_code == 200
    assert "access_token" in response.json()
    assert "refresh_token" in response.json()


@pytest.mark.asyncio
async def test_get_books(transport):
    from repository.mongo import get_database
    mock_db = make_mock_db()
    app.dependency_overrides[get_database] = lambda: mock_db

    token = get_token()
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        response = await ac.get("/api/books", headers={"Authorization": f"Bearer {token}"})
    app.dependency_overrides.clear()
    assert response.status_code == 200
    assert isinstance(response.json(), list)


@pytest.mark.asyncio
async def test_create_book(transport):
    from repository.mongo import get_database
    mock_db = make_mock_db()
    app.dependency_overrides[get_database] = lambda: mock_db

    token = get_token()
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        response = await ac.post("/api/books", json={
            "title": "Test Book",
            "author": "Author",
            "description": "Test description",
            "status": "available",
            "year": 2026
        }, headers={"Authorization": f"Bearer {token}"})
    app.dependency_overrides.clear()
    assert response.status_code == 200
    assert "id" in response.json()


@pytest.mark.asyncio
async def test_get_book_by_id(transport):
    from repository.mongo import get_database
    mock_db = make_mock_db()
    app.dependency_overrides[get_database] = lambda: mock_db

    token = get_token()
    book_id = str(FAKE_BOOK["_id"])
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        response = await ac.get(f"/api/books/{book_id}", headers={"Authorization": f"Bearer {token}"})
    app.dependency_overrides.clear()
    assert response.status_code == 200
    assert response.json()["id"] == book_id


@pytest.mark.asyncio
async def test_update_book(transport):
    from repository.mongo import get_database
    updated_book = {**FAKE_BOOK, "title": "New Title"}
    mock_db = make_mock_db(book=updated_book)
    app.dependency_overrides[get_database] = lambda: mock_db

    token = get_token()
    book_id = str(FAKE_BOOK["_id"])
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        response = await ac.put(f"/api/books/{book_id}", json={
            "title": "New Title",
            "author": "Author",
            "description": "Desc",
            "status": "borrowed",
            "year": 2026
        }, headers={"Authorization": f"Bearer {token}"})
    app.dependency_overrides.clear()
    assert response.status_code == 200
    assert response.json()["title"] == "New Title"


@pytest.mark.asyncio
async def test_delete_book(transport):
    from repository.mongo import get_database
    mock_db = make_mock_db()
    app.dependency_overrides[get_database] = lambda: mock_db

    token = get_token()
    book_id = str(FAKE_BOOK["_id"])
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        response = await ac.delete(f"/api/books/{book_id}", headers={"Authorization": f"Bearer {token}"})
    app.dependency_overrides.clear()
    assert response.status_code == 200


@pytest.mark.asyncio
async def test_book_not_found(transport):
    from repository.mongo import get_database
    mock_db = make_mock_db(book_found=False)
    app.dependency_overrides[get_database] = lambda: mock_db

    token = get_token()
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        response = await ac.get(f"/api/books/{NOT_FOUND_ID}", headers={"Authorization": f"Bearer {token}"})
    app.dependency_overrides.clear()
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_unauthorized_access(transport):
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        response = await ac.get("/api/books")
    assert response.status_code == 401