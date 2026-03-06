import uuid
import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_health(client: AsyncClient):
    r = await client.get("/api/health")
    assert r.status_code == 200
    assert r.json() == {"status": "ok"}


@pytest.mark.asyncio
async def test_get_all_books(client: AsyncClient):
    r = await client.get("/api/books")
    assert r.status_code == 200

    data = r.json()
    assert "items" in data
    assert "next_cursor" in data
    assert "limit" in data
    assert isinstance(data["items"], list)


@pytest.mark.asyncio
async def test_create_book(client: AsyncClient):
    payload = {
        "title": "Clean Code",
        "author": "Robert Martin",
        "description": "Demo",
        "status": "available",
        "year": 2008,
    }

    r = await client.post("/api/books", json=payload)
    assert r.status_code == 201

    data = r.json()
    assert data["title"] == payload["title"]
    assert data["author"] == payload["author"]
    assert "id" in data


@pytest.mark.asyncio
async def test_get_book_by_id(client: AsyncClient):
    payload = {
        "title": "Test Book",
        "author": "Author",
        "description": None,
        "status": "available",
        "year": 2010,
    }

    created = await client.post("/api/books", json=payload)
    book_id = created.json()["id"]

    r = await client.get(f"/api/books/{book_id}")

    assert r.status_code == 200
    assert r.json()["id"] == book_id


@pytest.mark.asyncio
async def test_get_book_404(client: AsyncClient):
    r = await client.get(f"/api/books/{uuid.uuid4()}")
    assert r.status_code == 404
    assert r.json()["detail"] == "Book not found"


@pytest.mark.asyncio
async def test_delete_idempotent(client: AsyncClient):
    created = await client.post(
        "/api/books",
        json={
            "title": "Delete Me",
            "author": "Author",
            "description": None,
            "status": "available",
            "year": 2010,
        },
    )
    book_id = created.json()["id"]

    r1 = await client.delete(f"/api/books/{book_id}")
    r2 = await client.delete(f"/api/books/{book_id}")

    assert r1.status_code == 204
    assert r2.status_code == 204


@pytest.mark.asyncio
async def test_cursor_pagination(client: AsyncClient):
    for i in range(5):
        await client.post(
            "/api/books",
            json={
                "title": f"Book {i}",
                "author": "Cursor Author",
                "description": None,
                "status": "available",
                "year": 2000 + i,
            },
        )

    first_page = await client.get("/api/books", params={"limit": 2, "sort_by": "year", "order": "asc"})
    assert first_page.status_code == 200

    first_data = first_page.json()
    assert len(first_data["items"]) <= 2
    assert "next_cursor" in first_data

    if first_data["next_cursor"]:
        second_page = await client.get(
            "/api/books",
            params={
                "limit": 2,
                "sort_by": "year",
                "order": "asc",
                "cursor": first_data["next_cursor"],
            },
        )
        assert second_page.status_code == 200


@pytest.mark.asyncio
async def test_filter_by_author(client: AsyncClient):
    await client.post(
        "/api/books",
        json={
            "title": "Author Test",
            "author": "Special Author",
            "description": None,
            "status": "available",
            "year": 2020,
        },
    )

    r = await client.get("/api/books", params={"author": "Special Author"})
    assert r.status_code == 200
    assert all(item["author"] == "Special Author" for item in r.json()["items"])


@pytest.mark.asyncio
async def test_filter_by_status(client: AsyncClient):
    await client.post(
        "/api/books",
        json={
            "title": "Issued Book",
            "author": "Status Author",
            "description": None,
            "status": "issued",
            "year": 2021,
        },
    )

    r = await client.get("/api/books", params={"status": "issued"})
    assert r.status_code == 200
    assert all(item["status"] == "issued" for item in r.json()["items"])


@pytest.mark.asyncio
async def test_sort_by_year_desc(client: AsyncClient):
    await client.post(
        "/api/books",
        json={
            "title": "Old Book",
            "author": "Sorter",
            "description": None,
            "status": "available",
            "year": 1999,
        },
    )
    await client.post(
        "/api/books",
        json={
            "title": "New Book",
            "author": "Sorter",
            "description": None,
            "status": "available",
            "year": 2023,
        },
    )

    r = await client.get(
        "/api/books",
        params={"author": "Sorter", "sort_by": "year", "order": "desc"},
    )
    assert r.status_code == 200

    years = [item["year"] for item in r.json()["items"]]
    assert years == sorted(years, reverse=True)


@pytest.mark.asyncio
async def test_validation_error(client: AsyncClient):
    r = await client.post(
        "/api/books",
        json={
            "title": "_BadTitle",
            "author": "A",
            "description": None,
            "status": "available",
            "year": 1200,
        },
    )
    assert r.status_code == 422