# aieo-api

FastAPI backend for AI Engineer OS.

## Develop

```bash
uv sync
cp .env.example .env
uv run alembic upgrade head
uv run uvicorn app.main:app --reload --port 8000
```

OpenAPI docs: http://localhost:8000/docs

## Tests / lint / typecheck

```bash
uv run ruff check .
uv run mypy .
uv run pytest
```
