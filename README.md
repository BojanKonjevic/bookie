# bookie

A self-hosted bookmark manager REST API. Save URLs, tag them, mark favorites, and search — all over a clean HTTP interface.

Built with **FastAPI**, **SQLAlchemy (async)**, and **PostgreSQL**, with a Nix-powered dev environment so setup is fully reproducible.

---

## Features

- **CRUD for bookmarks** — create, read, update, and delete bookmarks with title, URL, and optional description
- **Favorites** — flag any bookmark for quick retrieval
- **Tags** — attach multiple tags to bookmarks; tags are created automatically on first use
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

Edit `.env` if needed. For a local PostgreSQL database using peer auth, the default is fine:

```env
DATABASE_URL=postgresql+asyncpg:///bookie
```

For a remote or production database, replace the URL:

```env
DATABASE_URL=postgresql+asyncpg://user:pass@host:5432/dbname
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

## API Reference

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

Tags are referenced by name. New tag names are created automatically; existing ones are reused.

### Tags

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/tags` | List all tags |
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

1. Find the package: `nix search nixpkgs python3Packages.<name>`
2. Add it to `pythonEnv` in `flake.nix`
3. Add it to `dependencies` in `pyproject.toml`
4. Re-enter the shell: `exit`, then `nix develop`

---

## Project Layout

```
bookie/
├── src/bookie/
│   ├── main.py          # FastAPI app + router registration
│   ├── models.py        # SQLAlchemy ORM models
│   ├── schemas.py       # Pydantic request/response schemas
│   ├── crud.py          # Database operations
│   ├── database.py      # Async engine, session, lifespan
│   ├── settings.py      # Environment config (pydantic-settings)
│   └── routes/
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
