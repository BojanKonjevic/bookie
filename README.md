# bookie

## Development

Enter the dev shell:

```bash
nix develop
```

Once inside:

```bash
just test     # run tests
just cov      # with coverage
just lint     # lint
just fmt      # format
just check    # type check
just run      # run the app
```

## Database

Migrations are managed with Alembic. The local database is **PostgreSQL** using peer auth
(no password — connects as your OS user via Unix socket).

```bash
just migrate "initial schema"   # generate a migration
just upgrade                    # apply migrations
just downgrade                  # roll back one step
just db-drop                    # delete the local database entirely
```

The database (`bookie`) was created automatically when you ran the project scaffold script.

For a remote or production database, override `DATABASE_URL` in `.env`:
```
DATABASE_URL=postgresql+asyncpg://user:pass@host:5432/dbname
```

Define models in `src/bookie/models.py` — they are auto-imported by `alembic/env.py`.

## Setup

Copy the example env file and adjust as needed:

```bash
cp .env.example .env
```

## Adding dependencies

1. Find the package: `nix search nixpkgs python3Packages.<n>`
2. Add it to `pythonEnv` in `flake.nix`
3. Add it to `dependencies` in `pyproject.toml`
4. Re-enter the shell: `exit` then `nix develop`

## Project layout

```
flake.nix               ← Nix dev environment
pyproject.toml          ← Python project metadata + tool config
src/bookie/          ← Your source code
tests/                  ← Pytest tests
justfile                ← Short command aliases
.pre-commit-config.yaml ← Git hooks (auto-installed on nix develop)
.env.example            ← Committed env template (copy to .env)
```
