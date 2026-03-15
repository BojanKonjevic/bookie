# bookie

A self-hosted bookmark manager REST API. Save URLs, tag them, mark favorites, and search — all over a clean HTTP interface, with per-user data isolation via JWT authentication.

Built with **FastAPI**, **SQLAlchemy (async)**, and **PostgreSQL**, with a Nix-powered dev environment so setup is fully reproducible.

---

## Features

- **Auth** — register, log in, and receive a JWT access token; all data is scoped to the authenticated user
- **CRUD for bookmarks** — create, read, update, and delete bookmarks with title, URL, and optional description
- **Favorites** — flag any bookmark for quick retrieval
- **Tags** — attach multiple tags to bookmarks; tags are created automatically on first use and are per-user
- **Filtering & search** — filter by favorite status, one or more tags, or a search string; results are paginated
- **Async throughout** — fully async stack (asyncpg + SQLAlchemy async sessions)
- **Auto-generated docs** — FastAPI provides interactive Swagger UI out of the box at `/docs`

---

## Tech Stack

| Layer | Library |
|---|---|
| Web framework | FastAPI |
| ORM | SQLAlchemy 2 (async) |
| Database | PostgreSQL (asyncpg driver) |
| Migrations | Alembic |
| Validation | Pydantic v2 |
| Auth | JWT (python-jose) + bcrypt (passlib) |
| Dev environment | Nix flake |
| Task runner | just |
| Linting / formatting | Ruff |
| Type checking | mypy (strict) |
| Testing | pytest + pytest-asyncio |

---

## Getting Started

### Prerequisites

- [Nix](https://nixos.org/download/) with flakes enabled
- A local PostgreSQL instance (peer auth, no password)

### 1. Enter the dev shell

```bash
nix develop
```

This installs all dependencies and activates pre-commit hooks automatically.

### 2. Configure environment

```bash
cp .env.example .env
```

Edit `.env`. The database URL default is fine for local peer auth. Set a real secret key:

```env
DATABASE_URL=postgresql+asyncpg:///bookie
SECRET_KEY=your-long-random-secret-key
```

Generate a secure key with:

```bash
openssl rand -hex 32
```

### 3. Apply database migrations

```bash
just upgrade
```

### 4. Run the app

```bash
just run
```

The API will be available at `http://localhost:8000`. Visit `http://localhost:8000/docs` for the interactive API explorer.

---

## Authentication

All bookmark and tag endpoints require authentication. The flow is:

1. **Register** — `POST /auth/register` with an email and password
2. **Log in** — `POST /auth/token` to receive a JWT access token
3. **Authorize** — send the token as a `Bearer` header on subsequent requests

In the Swagger UI, use the **Authorize** button (top right) to log in and have the token attached automatically.

Tokens expire after 30 minutes by default (configurable via `ACCESS_TOKEN_EXPIRE_MINUTES` in `.env`).

---

## API Reference

### Auth

| Method | Endpoint | Auth required | Description |
|---|---|---|---|
| `POST` | `/auth/register` | No | Create a new account |
| `POST` | `/auth/token` | No | Log in and receive a JWT |
| `GET` | `/me` | Yes | Get the current user |

#### Register payload

```json
{ "email": "you@example.com", "password": "yourpassword" }
```

#### Token response

```json
{ "access_token": "eyJ...", "token_type": "bearer" }
```

### Bookmarks

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/bookmarks` | List bookmarks (supports filtering & pagination) |
| `GET` | `/bookmarks/{id}` | Get a single bookmark |
| `POST` | `/bookmarks` | Create a bookmark |
| `PATCH` | `/bookmarks/{id}` | Update a bookmark |
| `DELETE` | `/bookmarks/{id}` | Delete a bookmark |

#### Query parameters for `GET /bookmarks`

| Parameter | Type | Description |
|---|---|---|
| `favorite` | `bool` | Filter by favorite status |
| `tags` | `string[]` | Filter by one or more tag names |
| `search` | `string` | Search across titles and descriptions |
| `page` | `int` | Page number (default: `1`) |
| `limit` | `int` | Results per page (default: `10`, max: `100`) |

#### Bookmark object

```json
{
  "id": "uuid",
  "title": "FastAPI Docs",
  "url": "https://fastapi.tiangolo.com",
  "description": "Official FastAPI documentation",
  "favorite": false,
  "created_at": "2024-01-15T10:30:00Z",
  "tags": [
    { "id": "uuid", "name": "python" },
    { "id": "uuid", "name": "docs" }
  ]
}
```

#### Create / update payload

```json
{
  "title": "FastAPI Docs",
  "url": "https://fastapi.tiangolo.com",
  "description": "Optional description",
  "favorite": false,
  "tags": ["python", "docs"]
}
```

Tags are referenced by name. New tag names are created automatically; existing ones are reused. Tags are scoped to the authenticated user.

### Tags

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/tags` | List all tags for the current user |
| `GET` | `/tags/{id}` | Get a single tag |

---

## Development

All common tasks are available via `just`:

```bash
just test     # run tests
just cov      # run tests with coverage report
just lint     # lint with Ruff
just fmt      # format with Ruff
just check    # type check with mypy
just run      # start the dev server with auto-reload
```

### Database

```bash
just migrate "description"   # generate a new migration
just upgrade                 # apply all pending migrations
just downgrade               # roll back one migration
just db-drop                 # drop the local database entirely
```

Models are defined in `src/bookie/models.py` and are auto-imported by Alembic.

### Adding dependencies

1. Find the package: `nix search nixpkgs python3Packages.<n>`
2. Add it to `pythonEnv` in `flake.nix`
3. Add it to `dependencies` in `pyproject.toml`
4. Re-enter the shell: `exit`, then `nix develop`

---

## Project Layout

```
bookie/
├── src/bookie/
│   ├── main.py          # FastAPI app + router registration
│   ├── models.py        # SQLAlchemy ORM models (User, Bookmark, Tag)
│   ├── schemas.py       # Pydantic request/response schemas
│   ├── crud.py          # Database operations
│   ├── database.py      # Async engine, session, lifespan
│   ├── settings.py      # Environment config (pydantic-settings)
│   ├── security.py      # Password hashing and JWT encode/decode
│   ├── dependencies.py  # get_current_user FastAPI dependency
│   └── routes/
│       ├── auth.py      # Register, login endpoints
│       ├── bookmarks.py # Bookmark endpoints
│       └── tags.py      # Tag endpoints
├── tests/               # Pytest test suite
├── alembic/             # Migration scripts
├── flake.nix            # Nix dev environment
├── pyproject.toml       # Project metadata + tool config
├── justfile             # Task runner aliases
├── alembic.ini          # Alembic config
├── .env.example         # Environment variable template
└── .pre-commit-config.yaml
```

