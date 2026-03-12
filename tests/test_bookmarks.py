from httpx import AsyncClient

# ─── POST /bookmarks ──────────────────────────────────────────────────────────


async def test_create_bookmark(client: AsyncClient) -> None:
    response = await client.post(
        "/bookmarks",
        json={
            "title": "FastAPI Docs",
            "url": "https://fastapi.tiangolo.com",
            "tags": ["python", "fastapi"],
        },
    )

    assert response.status_code == 201

    data = response.json()
    assert data["title"] == "FastAPI Docs"
    # Pydantic's HttpUrl normalises bare domains by appending a trailing slash.
    assert data["url"] == "https://fastapi.tiangolo.com/"
    assert data["favorite"] is False
    assert data["description"] is None
    assert len(data["tags"]) == 2
    tag_names = {t["name"] for t in data["tags"]}
    assert tag_names == {"python", "fastapi"}
    assert "id" in data
    assert "created_at" in data


async def test_create_bookmark_no_tags(client: AsyncClient) -> None:
    response = await client.post(
        "/bookmarks",
        json={"title": "No Tags", "url": "https://notags.example.com"},
    )

    assert response.status_code == 201
    assert response.json()["tags"] == []


async def test_create_bookmark_with_description(client: AsyncClient) -> None:
    response = await client.post(
        "/bookmarks",
        json={
            "title": "Described",
            "url": "https://described.example.com",
            "description": "A useful link",
        },
    )

    assert response.status_code == 201
    assert response.json()["description"] == "A useful link"


async def test_create_bookmark_as_favorite(client: AsyncClient) -> None:
    response = await client.post(
        "/bookmarks",
        json={
            "title": "Fav",
            "url": "https://fav.example.com",
            "favorite": True,
        },
    )

    assert response.status_code == 201
    assert response.json()["favorite"] is True


async def test_create_bookmark_deduplicates_tags_in_same_request(
    client: AsyncClient,
) -> None:
    # Sending the same tag name twice should still produce one tag.
    response = await client.post(
        "/bookmarks",
        json={
            "title": "Dupe Tags",
            "url": "https://dupetags.example.com",
            "tags": ["python", "python"],
        },
    )

    assert response.status_code == 201
    assert len(response.json()["tags"]) == 1


async def test_create_bookmark_reuses_existing_tag(client: AsyncClient) -> None:
    # Both bookmarks share the "python" tag — it should be one row in the DB,
    # not two separate Tag rows with the same name.
    await client.post(
        "/bookmarks",
        json={"title": "First", "url": "https://first.example.com", "tags": ["python"]},
    )
    response = await client.post(
        "/bookmarks",
        json={
            "title": "Second",
            "url": "https://second.example.com",
            "tags": ["python"],
        },
    )

    assert response.status_code == 201

    # The tags list endpoint shows all tags — should still be just one "python".
    tags_response = await client.get("/tags")
    python_tags = [t for t in tags_response.json() if t["name"] == "python"]
    assert len(python_tags) == 1


async def test_create_bookmark_missing_title(client: AsyncClient) -> None:
    response = await client.post(
        "/bookmarks",
        json={"url": "https://notable.example.com"},
    )
    assert response.status_code == 422


async def test_create_bookmark_empty_title(client: AsyncClient) -> None:
    # min_length=1 is set on BookmarkBase.title
    response = await client.post(
        "/bookmarks",
        json={"title": "", "url": "https://emptytitle.example.com"},
    )
    assert response.status_code == 422


async def test_create_bookmark_missing_url(client: AsyncClient) -> None:
    response = await client.post("/bookmarks", json={"title": "No URL"})
    assert response.status_code == 422


async def test_create_bookmark_invalid_url(client: AsyncClient) -> None:
    response = await client.post(
        "/bookmarks",
        json={"title": "Bad URL", "url": "not-a-url"},
    )
    assert response.status_code == 422


async def test_create_bookmark_duplicate_url(client: AsyncClient) -> None:
    payload = {"title": "Original", "url": "https://duplicate.example.com"}
    await client.post("/bookmarks", json=payload)
    response = await client.post("/bookmarks", json={**payload, "title": "Duplicate"})
    assert response.status_code == 409


# ─── GET /bookmarks/{id} ──────────────────────────────────────────────────────


async def test_get_bookmark(client: AsyncClient, bookmark: dict) -> None:
    response = await client.get(f"/bookmarks/{bookmark['id']}")

    assert response.status_code == 200

    data = response.json()
    assert data["id"] == bookmark["id"]
    assert data["title"] == bookmark["title"]
    assert data["url"] == bookmark["url"]


async def test_get_bookmark_not_found(client: AsyncClient) -> None:
    fake_id = "00000000-0000-0000-0000-000000000000"
    response = await client.get(f"/bookmarks/{fake_id}")
    assert response.status_code == 404


async def test_get_bookmark_invalid_uuid(client: AsyncClient) -> None:
    response = await client.get("/bookmarks/not-a-uuid")
    assert response.status_code == 422


# ─── GET /bookmarks ───────────────────────────────────────────────────────────


async def test_get_all_bookmarks_empty(client: AsyncClient) -> None:
    response = await client.get("/bookmarks")
    assert response.status_code == 200
    assert response.json() == []


async def test_get_all_bookmarks(client: AsyncClient) -> None:
    await client.post(
        "/bookmarks",
        json={"title": "First", "url": "https://first.example.com"},
    )
    await client.post(
        "/bookmarks",
        json={"title": "Second", "url": "https://second.example.com"},
    )

    response = await client.get("/bookmarks")

    assert response.status_code == 200
    assert len(response.json()) == 2


async def test_get_all_bookmarks_filter_favorites(client: AsyncClient) -> None:
    await client.post(
        "/bookmarks",
        json={
            "title": "Not Fav",
            "url": "https://notfav.example.com",
            "favorite": False,
        },
    )
    await client.post(
        "/bookmarks",
        json={"title": "Is Fav", "url": "https://isfav.example.com", "favorite": True},
    )

    response = await client.get("/bookmarks", params={"favorite": "true"})

    assert response.status_code == 200
    results = response.json()
    assert len(results) == 1
    assert results[0]["title"] == "Is Fav"


async def test_get_all_bookmarks_filter_non_favorites(client: AsyncClient) -> None:
    await client.post(
        "/bookmarks",
        json={
            "title": "Not Fav",
            "url": "https://notfav2.example.com",
            "favorite": False,
        },
    )
    await client.post(
        "/bookmarks",
        json={"title": "Is Fav", "url": "https://isfav2.example.com", "favorite": True},
    )

    response = await client.get("/bookmarks", params={"favorite": "false"})

    assert response.status_code == 200
    results = response.json()
    assert len(results) == 1
    assert results[0]["title"] == "Not Fav"


async def test_get_all_bookmarks_filter_by_tag(client: AsyncClient) -> None:
    await client.post(
        "/bookmarks",
        json={
            "title": "Python",
            "url": "https://python.example.com",
            "tags": ["python"],
        },
    )
    await client.post(
        "/bookmarks",
        json={"title": "Rust", "url": "https://rust.example.com", "tags": ["rust"]},
    )

    response = await client.get("/bookmarks", params={"tags": "python"})

    assert response.status_code == 200
    results = response.json()
    assert len(results) == 1
    assert results[0]["title"] == "Python"


async def test_get_all_bookmarks_filter_by_tag_returns_any_match(
    client: AsyncClient,
) -> None:
    # Tag filter is OR — a bookmark matching ANY of the given tags is returned.
    await client.post(
        "/bookmarks",
        json={
            "title": "Python",
            "url": "https://pytag.example.com",
            "tags": ["python"],
        },
    )
    await client.post(
        "/bookmarks",
        json={"title": "Rust", "url": "https://rusttag.example.com", "tags": ["rust"]},
    )
    await client.post(
        "/bookmarks",
        json={"title": "Go", "url": "https://gotag.example.com", "tags": ["go"]},
    )

    response = await client.get("/bookmarks", params={"tags": ["python", "rust"]})

    assert response.status_code == 200
    titles = {b["title"] for b in response.json()}
    assert titles == {"Python", "Rust"}


async def test_get_all_bookmarks_search_matches_title(client: AsyncClient) -> None:
    await client.post(
        "/bookmarks",
        json={"title": "SQLAlchemy Guide", "url": "https://sqla.example.com"},
    )
    await client.post(
        "/bookmarks",
        json={"title": "Unrelated", "url": "https://unrelated.example.com"},
    )

    response = await client.get("/bookmarks", params={"search": "sqlalchemy"})

    assert response.status_code == 200
    results = response.json()
    assert len(results) == 1
    assert results[0]["title"] == "SQLAlchemy Guide"


async def test_get_all_bookmarks_search_matches_description(
    client: AsyncClient,
) -> None:
    await client.post(
        "/bookmarks",
        json={
            "title": "Something",
            "url": "https://searchdesc.example.com",
            "description": "All about async programming",
        },
    )
    await client.post(
        "/bookmarks",
        json={"title": "Other", "url": "https://other.example.com"},
    )

    response = await client.get("/bookmarks", params={"search": "async"})

    assert response.status_code == 200
    results = response.json()
    assert len(results) == 1
    assert results[0]["title"] == "Something"


async def test_get_all_bookmarks_search_is_case_insensitive(
    client: AsyncClient,
) -> None:
    await client.post(
        "/bookmarks",
        json={"title": "FastAPI Tutorial", "url": "https://casesearch.example.com"},
    )

    response = await client.get("/bookmarks", params={"search": "FASTAPI"})

    assert response.status_code == 200
    assert len(response.json()) == 1


async def test_get_all_bookmarks_pagination(client: AsyncClient) -> None:
    for i in range(5):
        await client.post(
            "/bookmarks",
            json={"title": f"Bookmark {i}", "url": f"https://page{i}.example.com"},
        )

    page1 = await client.get("/bookmarks", params={"page": 1, "limit": 3})
    page2 = await client.get("/bookmarks", params={"page": 2, "limit": 3})

    assert len(page1.json()) == 3
    assert len(page2.json()) == 2

    # No overlap between pages.
    page1_ids = {b["id"] for b in page1.json()}
    page2_ids = {b["id"] for b in page2.json()}
    assert page1_ids.isdisjoint(page2_ids)


async def test_get_all_bookmarks_limit_validation(client: AsyncClient) -> None:
    # limit has ge=1, le=100 set on the Query param
    response = await client.get("/bookmarks", params={"limit": 0})
    assert response.status_code == 422

    response = await client.get("/bookmarks", params={"limit": 101})
    assert response.status_code == 422


async def test_get_all_bookmarks_page_validation(client: AsyncClient) -> None:
    # page has ge=1
    response = await client.get("/bookmarks", params={"page": 0})
    assert response.status_code == 422


# ─── PATCH /bookmarks/{id} ────────────────────────────────────────────────────


async def test_update_bookmark_title(client: AsyncClient, bookmark: dict) -> None:
    response = await client.patch(
        f"/bookmarks/{bookmark['id']}",
        json={"title": "Updated Title"},
    )

    assert response.status_code == 200
    assert response.json()["title"] == "Updated Title"
    # Other fields must be unchanged.
    assert response.json()["url"] == bookmark["url"]


async def test_update_bookmark_favorite(client: AsyncClient, bookmark: dict) -> None:
    response = await client.patch(
        f"/bookmarks/{bookmark['id']}",
        json={"favorite": True},
    )

    assert response.status_code == 200
    assert response.json()["favorite"] is True


async def test_update_bookmark_description(client: AsyncClient, bookmark: dict) -> None:
    response = await client.patch(
        f"/bookmarks/{bookmark['id']}",
        json={"description": "New description"},
    )

    assert response.status_code == 200
    assert response.json()["description"] == "New description"


async def test_update_bookmark_tags_replaces_all(
    client: AsyncClient, bookmark: dict
) -> None:
    # The fixture bookmark has ["test"]. Sending new tags should replace, not append.
    response = await client.patch(
        f"/bookmarks/{bookmark['id']}",
        json={"tags": ["newone", "newtwo"]},
    )

    assert response.status_code == 200
    tag_names = {t["name"] for t in response.json()["tags"]}
    assert tag_names == {"newone", "newtwo"}
    assert "test" not in tag_names


async def test_update_bookmark_clear_tags(client: AsyncClient, bookmark: dict) -> None:
    response = await client.patch(
        f"/bookmarks/{bookmark['id']}",
        json={"tags": []},
    )

    assert response.status_code == 200
    assert response.json()["tags"] == []


async def test_update_bookmark_not_found(client: AsyncClient) -> None:
    fake_id = "00000000-0000-0000-0000-000000000000"
    response = await client.patch(f"/bookmarks/{fake_id}", json={"title": "Ghost"})
    assert response.status_code == 404


# ─── DELETE /bookmarks/{id} ───────────────────────────────────────────────────


async def test_delete_bookmark(client: AsyncClient, bookmark: dict) -> None:
    response = await client.delete(f"/bookmarks/{bookmark['id']}")
    assert response.status_code == 204

    # Confirm it's gone.
    follow_up = await client.get(f"/bookmarks/{bookmark['id']}")
    assert follow_up.status_code == 404


async def test_delete_bookmark_not_found(client: AsyncClient) -> None:
    fake_id = "00000000-0000-0000-0000-000000000000"
    response = await client.delete(f"/bookmarks/{fake_id}")
    assert response.status_code == 404


async def test_delete_bookmark_removes_orphan_tag(client: AsyncClient) -> None:
    # "orphan" tag belongs only to this one bookmark.
    # After the bookmark is deleted the tag should be gone too.
    response = await client.post(
        "/bookmarks",
        json={"title": "Solo", "url": "https://solo.example.com", "tags": ["orphan"]},
    )
    bookmark_id = response.json()["id"]

    await client.delete(f"/bookmarks/{bookmark_id}")

    tags = await client.get("/tags")
    tag_names = [t["name"] for t in tags.json()]
    assert "orphan" not in tag_names


async def test_delete_bookmark_keeps_shared_tag(client: AsyncClient) -> None:
    # "shared" tag belongs to two bookmarks.
    # Deleting one bookmark must NOT delete the tag.
    r1 = await client.post(
        "/bookmarks",
        json={"title": "A", "url": "https://shared-a.example.com", "tags": ["shared"]},
    )
    await client.post(
        "/bookmarks",
        json={"title": "B", "url": "https://shared-b.example.com", "tags": ["shared"]},
    )

    await client.delete(f"/bookmarks/{r1.json()['id']}")

    tags = await client.get("/tags")
    tag_names = [t["name"] for t in tags.json()]
    assert "shared" in tag_names
