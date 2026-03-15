from httpx import AsyncClient

TEST_USER = {"email": "test@example.com", "password": "testpassword123"}

# ─── POST /auth/register ──────────────────────────────────────────────────────


async def test_register(anon_client: AsyncClient) -> None:
    response = await anon_client.post("/auth/register", json=TEST_USER)

    assert response.status_code == 201

    data = response.json()
    assert data["email"] == TEST_USER["email"]
    assert data["is_active"] is True
    assert "id" in data
    # Password must never appear in a response.
    assert "password" not in data
    assert "hashed_password" not in data


async def test_register_duplicate_email(anon_client: AsyncClient) -> None:
    await anon_client.post("/auth/register", json=TEST_USER)
    response = await anon_client.post("/auth/register", json=TEST_USER)
    assert response.status_code == 409


async def test_register_invalid_email(anon_client: AsyncClient) -> None:
    response = await anon_client.post(
        "/auth/register", json={"email": "not-an-email", "password": "password123"}
    )
    assert response.status_code == 422


async def test_register_missing_password(anon_client: AsyncClient) -> None:
    response = await anon_client.post(
        "/auth/register", json={"email": "user@example.com"}
    )
    assert response.status_code == 422


# ─── POST /auth/token ─────────────────────────────────────────────────────────


async def test_login(anon_client: AsyncClient) -> None:
    await anon_client.post("/auth/register", json=TEST_USER)

    response = await anon_client.post(
        "/auth/token",
        data={"username": TEST_USER["email"], "password": TEST_USER["password"]},
    )

    assert response.status_code == 200

    data = response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"


async def test_login_wrong_password(anon_client: AsyncClient) -> None:
    await anon_client.post("/auth/register", json=TEST_USER)

    response = await anon_client.post(
        "/auth/token",
        data={"username": TEST_USER["email"], "password": "wrongpassword"},
    )

    assert response.status_code == 401


async def test_login_unknown_email(anon_client: AsyncClient) -> None:
    response = await anon_client.post(
        "/auth/token",
        data={"username": "nobody@example.com", "password": "password123"},
    )
    assert response.status_code == 401


# ─── GET /me ──────────────────────────────────────────────────────────────────


async def test_get_me(client: AsyncClient) -> None:
    response = await client.get("/me")

    assert response.status_code == 200

    data = response.json()
    assert data["email"] == TEST_USER["email"]
    assert data["is_active"] is True


async def test_get_me_unauthenticated(anon_client: AsyncClient) -> None:
    response = await anon_client.get("/me")
    assert response.status_code == 401


async def test_get_me_invalid_token(anon_client: AsyncClient) -> None:
    anon_client.headers["Authorization"] = "Bearer this.is.not.a.valid.token"
    response = await anon_client.get("/me")
    assert response.status_code == 401


# ─── Auth isolation ───────────────────────────────────────────────────────────


async def test_users_cannot_see_each_others_bookmarks(
    client: AsyncClient, anon_client: AsyncClient
) -> None:
    # Create a bookmark as the primary test user.
    await client.post(
        "/bookmarks",
        json={"title": "Private", "url": "https://private.example.com"},
    )

    # Register and log in as a second user.
    second_user = {"email": "other@example.com", "password": "otherpassword123"}
    await anon_client.post("/auth/register", json=second_user)
    token_resp = await anon_client.post(
        "/auth/token",
        data={"username": second_user["email"], "password": second_user["password"]},
    )
    anon_client.headers["Authorization"] = f"Bearer {token_resp.json()['access_token']}"

    response = await anon_client.get("/bookmarks")
    assert response.status_code == 200
    assert response.json() == []
