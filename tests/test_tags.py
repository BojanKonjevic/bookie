from httpx import AsyncClient

# Tags have no create/update/delete endpoints of their own — they are managed
# entirely through bookmarks. These tests cover the read endpoints only.


async def test_get_all_tags_empty(client: AsyncClient) -> None:
    response = await client.get("/tags")
    assert response.status_code == 200
    assert response.json() == []


async def test_get_all_tags(client: AsyncClient) -> None:
    await client.post(
        "/bookmarks",
        json={
            "title": "A",
            "url": "https://tagsa.example.com",
            "tags": ["alpha", "beta"],
        },
    )
    await client.post(
        "/bookmarks",
        json={
            "title": "B",
            "url": "https://tagsb.example.com",
            "tags": ["beta", "gamma"],
        },
    )

    response = await client.get("/tags")

    assert response.status_code == 200

    names = {t["name"] for t in response.json()}
    # "beta" appears on two bookmarks but should only be one tag row.
    assert names == {"alpha", "beta", "gamma"}
    assert len(response.json()) == 3


async def test_get_tag(client: AsyncClient) -> None:
    await client.post(
        "/bookmarks",
        json={
            "title": "Tagged",
            "url": "https://tagged.example.com",
            "tags": ["mytag"],
        },
    )

    # Fetch the tag's ID from the list endpoint, then look it up directly.
    all_tags = (await client.get("/tags")).json()
    tag = next(t for t in all_tags if t["name"] == "mytag")

    response = await client.get(f"/tags/{tag['id']}")

    assert response.status_code == 200
    assert response.json()["id"] == tag["id"]
    assert response.json()["name"] == "mytag"


async def test_get_tag_not_found(client: AsyncClient) -> None:
    fake_id = "00000000-0000-0000-0000-000000000000"
    response = await client.get(f"/tags/{fake_id}")
    assert response.status_code == 404
    assert response.json()["detail"] == "Tag doesn't exist"


async def test_get_tag_invalid_uuid(client: AsyncClient) -> None:
    response = await client.get("/tags/not-a-uuid")
    assert response.status_code == 422
