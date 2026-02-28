from __future__ import annotations

import pytest
from httpx import AsyncClient, ASGITransport

from main import app

from models.book_model import db

@pytest.fixture
async def client():
    db.clear()
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac


@pytest.mark.asyncio
async def test_health(client: AsyncClient):
    r = await client.get("/api/healt")
    assert r.status_code == 200
    assert r.json() == {"status": "ok"}


@pytest.mark.asyncio
async def test_create_book_201_and_get_by_id_200(client: AsyncClient):
    payload = {
        "title": "Clean Code",
        "author": "Robert C. Martin",
        "description": "Agile craftsmanship",
        "status": "available",
        "year": 2008,
    }
    created = await client.post("/api/books", json=payload)
    assert created.status_code == 201
    body = created.json()
    assert "id" in body
    assert body["title"] == payload["title"]
    assert body["author"] == payload["author"]
    assert body["description"] == payload["description"]
    assert body["status"] == payload["status"]
    assert body["year"] == payload["year"]

    book_id = body["id"]
    got = await client.get(f"/api/books/{book_id}")
    assert got.status_code == 200
    got_body = got.json()
    assert got_body["id"] == book_id
    assert got_body["title"] == payload["title"]


@pytest.mark.asyncio
async def test_get_by_id_404(client: AsyncClient):
    r = await client.get("/api/books/00000000-0000-0000-0000-000000000000")
    assert r.status_code == 404
    assert r.json()["detail"] == "Book not found"


@pytest.mark.asyncio
async def test_delete_idempotent_204_and_then_404_on_get(client: AsyncClient):
    created = await client.post("/api/books", json={
        "title": "To Delete",
        "author": "Someone",
        "description": None,
        "status": "available",
        "year": 2010,
    })
    book_id = created.json()["id"]

    d1 = await client.delete(f"/api/books/{book_id}")
    assert d1.status_code == 204
    assert d1.text == ""

    d2 = await client.delete(f"/api/books/{book_id}")
    assert d2.status_code == 204
    assert d2.text == ""

    g = await client.get(f"/api/books/{book_id}")
    assert g.status_code == 404


@pytest.mark.asyncio
async def test_get_all_200_returns_list(client: AsyncClient):
    r = await client.get("/api/books")
    assert r.status_code == 200
    data = r.json()
    assert isinstance(data, list)


@pytest.mark.asyncio
async def test_filter_by_author(client: AsyncClient):
    await client.post("/api/books", json={
        "title": "A1",
        "author": "Author X",
        "description": None,
        "status": "available",
        "year": 2001,
    })
    await client.post("/api/books", json={
        "title": "A2",
        "author": "Author Y",
        "description": None,
        "status": "available",
        "year": 2002,
    })

    r = await client.get("/api/books", params={"author": "Author X"})
    assert r.status_code == 200
    data = r.json()
    assert all(item["author"] == "Author X" for item in data)


@pytest.mark.asyncio
async def test_filter_by_status(client: AsyncClient):
    await client.post("/api/books", json={
        "title": "S1",
        "author": "Status Author",
        "description": None,
        "status": "issued",
        "year": 2003,
    })
    await client.post("/api/books", json={
        "title": "S2",
        "author": "Status Author",
        "description": None,
        "status": "available",
        "year": 2004,
    })

    r = await client.get("/api/books", params={"status": "issued"})
    assert r.status_code == 200
    data = r.json()
    assert len(data) >= 1
    assert all(item["status"] == "issued" for item in data)


@pytest.mark.asyncio
async def test_sort_by_title_asc_and_desc(client: AsyncClient):
    await client.post("/api/books", json={"title": "ccc", "author": "Sorter", "description": None, "status": "available", "year": 2001})
    await client.post("/api/books", json={"title": "aaa", "author": "Sorter", "description": None, "status": "available", "year": 2002})
    await client.post("/api/books", json={"title": "bbb", "author": "Sorter", "description": None, "status": "available", "year": 2003})

    r1 = await client.get("/api/books", params={"author": "Sorter", "sort_by": "title", "order": "asc"})
    assert r1.status_code == 200
    titles_asc = [x["title"] for x in r1.json()]
    assert titles_asc == sorted(titles_asc, key=lambda s: s.lower())

    r2 = await client.get("/api/books", params={"author": "Sorter", "sort_by": "title", "order": "desc"})
    assert r2.status_code == 200
    titles_desc = [x["title"] for x in r2.json()]
    assert titles_desc == sorted(titles_desc, key=lambda s: s.lower(), reverse=True)


@pytest.mark.asyncio
async def test_sort_by_year_asc_and_desc(client: AsyncClient):
    await client.post("/api/books", json={"title": "Y1", "author": "YearSorter", "description": None, "status": "available", "year": 1999})
    await client.post("/api/books", json={"title": "Y2", "author": "YearSorter", "description": None, "status": "available", "year": 2010})
    await client.post("/api/books", json={"title": "Y3", "author": "YearSorter", "description": None, "status": "available", "year": 2005})

    r1 = await client.get("/api/books", params={"author": "YearSorter", "sort_by": "year", "order": "asc"})
    years_asc = [x["year"] for x in r1.json()]
    assert years_asc == sorted(years_asc)

    r2 = await client.get("/api/books", params={"author": "YearSorter", "sort_by": "year", "order": "desc"})
    years_desc = [x["year"] for x in r2.json()]
    assert years_desc == sorted(years_desc, reverse=True)


@pytest.mark.asyncio
async def test_validation_422_title_underscore(client: AsyncClient):
    r = await client.post("/api/books", json={
        "title": "_Bad",
        "author": "Ok Author",
        "description": None,
        "status": "available",
        "year": 2020,
    })
    assert r.status_code == 422


@pytest.mark.asyncio
async def test_validation_422_short_author_and_year_range(client: AsyncClient):
    r = await client.post("/api/books", json={
        "title": "Good title",
        "author": "A",
        "description": None,
        "status": "available",
        "year": 1200,
    })
    assert r.status_code == 422


@pytest.mark.asyncio
async def test_query_param_validation_422_sort_by_invalid(client: AsyncClient):
    r = await client.get("/api/books", params={"sort_by": "author"})
    assert r.status_code == 422


@pytest.mark.asyncio
async def test_query_param_validation_422_order_invalid(client: AsyncClient):
    r = await client.get("/api/books", params={"order": "up"})
    assert r.status_code == 422