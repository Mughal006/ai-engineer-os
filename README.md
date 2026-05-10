# AI Engineer OS

An AI-powered learning platform that turns beginners into job-ready AI engineers.
Adaptive roadmaps, mastery-based progression, AI tutoring, simulated interviews,
coding sandbox, productivity analytics, and anti-cheat — in one product.

> Status: Week-1 MVP scaffold. Auth + DB schema + Roadmap Generator (stubbed AI) + minimal dashboard.

## Repo layout

```
ai-engineer-os/
├── apps/
│   ├── api/        FastAPI + SQLAlchemy + Alembic (Python 3.12)
│   └── web/        Next.js 14 + TypeScript + Tailwind + shadcn/ui
├── docker-compose.yml   Postgres for local dev
└── .github/workflows/   CI
```

## Quick start

### 1. Postgres

```bash
docker compose up -d postgres
```

### 2. API (FastAPI)

```bash
cd apps/api
cp .env.example .env             # fill in CLERK_SECRET_KEY etc.
uv sync                          # or: pip install -e .
uv run alembic upgrade head
uv run uvicorn app.main:app --reload --port 8000
```

API will be at http://localhost:8000, OpenAPI docs at http://localhost:8000/docs.

### 3. Web (Next.js)

```bash
cd apps/web
cp .env.example .env.local       # fill in NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY etc.
pnpm install
pnpm dev
```

Web will be at http://localhost:3000.

## Environment variables

### apps/api/.env

| Name | Description |
| --- | --- |
| `DATABASE_URL` | Postgres connection string. Default: `postgresql+psycopg://aieo:aieo@localhost:5432/aieo` |
| `CLERK_SECRET_KEY` | Clerk backend key, used to verify JWTs |
| `CLERK_JWT_ISSUER` | Clerk JWT issuer URL (e.g. `https://your-app.clerk.accounts.dev`) |
| `OPENAI_API_KEY` | Optional. When unset, the Roadmap Generator returns a deterministic stub. |
| `CORS_ORIGINS` | Comma-separated list. Default: `http://localhost:3000` |

### apps/web/.env.local

| Name | Description |
| --- | --- |
| `NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY` | Clerk publishable key |
| `CLERK_SECRET_KEY` | Clerk secret key (server actions) |
| `NEXT_PUBLIC_API_URL` | URL of FastAPI backend. Default: `http://localhost:8000` |

## What's built (Week 1)

- [x] Monorepo scaffold
- [x] Postgres schema + Alembic migration for the 8 core tables in the spec
- [x] FastAPI app with health check, Clerk JWT auth middleware, CORS
- [x] `POST /roadmaps` — generates a personalized plan from a skill assessment, persists it
- [x] `GET /roadmaps/me` — fetch the current user's active roadmap
- [x] Next.js app with Clerk auth, skill-assessment form, roadmap viewer, daily task list
- [x] CI: ruff + mypy + pytest for api; eslint + tsc for web

## Roadmap (next weeks)

Tracking the spec's "Suggested Development Order":

1. ✅ Authentication
2. ✅ Database
3. ✅ Roadmap Generator
4. ⏳ Learning Pages
5. ⏳ Quiz Engine
6. ⏳ Progress Tracking
7. ⏳ AI Tutor
8. ⏳ Interview Agent
9. ⏳ Coding Sandbox
10. ⏳ Analytics
11. ⏳ Monitoring System
12. ⏳ Advanced Agents

## License

TBD.
