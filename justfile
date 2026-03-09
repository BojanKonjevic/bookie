test:
    pytest -v
cov:
    pytest --cov=src --cov-report=term-missing
lint:
    ruff check .
fmt:
    ruff format .
check:
    mypy .
run:
    uvicorn bookie.main:app --reload

migrate msg="":
    alembic revision --autogenerate -m "{{msg}}"
upgrade:
    alembic upgrade head
downgrade:
    alembic downgrade -1
db-drop:
    dropdb bookie
