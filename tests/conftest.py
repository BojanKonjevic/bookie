import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from bookie.database import Base, get_session
from bookie.main import app

TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"


@pytest.fixture
async def session() -> AsyncSession:  # type: ignore[misc]
    engine = create_async_engine(TEST_DATABASE_URL)

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    factory = async_sessionmaker(engine, expire_on_commit=False)

    async with factory() as s:
        yield s

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)

    await engine.dispose()


@pytest.fixture
async def client(session: AsyncSession) -> AsyncClient:  # type: ignore[misc]
    async def override_get_session() -> AsyncSession:  # type: ignore[misc]
        yield session

    app.dependency_overrides[get_session] = override_get_session

    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test",
    ) as ac:
        yield ac

    app.dependency_overrides.clear()


# A pre-created bookmark that any test can request as a fixture dependency.
# Tests that need a bookmark to already exist use this instead of repeating
# the POST setup themselves.
@pytest.fixture
async def bookmark(client: AsyncClient) -> dict:  # type: ignore[misc]
    response = await client.post(
        "/bookmarks",
        json={
            "title": "Test Bookmark",
            "url": "https://example.com",
            "tags": ["test"],
        },
    )
    assert response.status_code == 201
    return response.json()
