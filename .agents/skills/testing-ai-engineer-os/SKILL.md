---
name: testing-ai-engineer-os
description: End-to-end test the AI Engineer OS roadmap flow locally. Use when verifying any change touching auth, the roadmap generator, persistence, or the dashboard / roadmap pages.
---

# Testing AI Engineer OS

## Stack & ports

- Postgres on `localhost:5432` via `docker compose up -d postgres` from repo root.
- FastAPI on `http://localhost:8000` from `apps/api` via `uv run uvicorn app.main:app --port 8000`.
- Next.js on `http://localhost:3000` from `apps/web` via `pnpm dev`.
- Health check: `curl http://localhost:8000/healthz`.

## Env files

- `apps/api/.env`: leave `CLERK_SECRET_KEY` and `CLERK_JWT_ISSUER` empty for local testing — the API falls back to a deterministic `dev-user` row (`apps/api/app/auth.py`). Keep `DATABASE_URL=postgresql+psycopg://aieo:aieo@localhost:5432/aieo`.
- `apps/web/.env.local`: needs real `NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY` and `CLERK_SECRET_KEY` (see Devin Secrets), plus `NEXT_PUBLIC_API_URL=http://localhost:8000`.

## Devin secrets needed

- `CLERK_PUBLISHABLE_KEY` (org scope) — for `apps/web/.env.local`.
- `CLERK_SECRET_KEY` (org scope) — for `apps/web/.env.local`. The API does NOT need this set; leaving it empty triggers the dev-user fallback.

## Clerk Turnstile workaround

Clerk's dev-instance Cloudflare Turnstile widget often hangs in headless / automation environments — the sign-up "Continue" button stays stuck on a spinner after the human-verification checkbox is clicked. This blocks automated UI sign-up.

If you need to drive the flow without going through Clerk:

1. Edit `apps/web/src/middleware.ts` and add `/onboarding(.*)`, `/dashboard(.*)`, `/roadmap(.*)` to `isPublicRoute`. **This is a test-only edit — revert it before exiting test mode and never commit it.**
2. Restart `pnpm dev` (or rely on Next hot-reload).
3. Navigate directly to `http://localhost:3000/onboarding`. The data path still works because `apps/web/src/lib/api.ts` already wraps `auth().getToken()` in try/catch (so a missing Clerk session is fine), and the API falls back to dev-user.

This bypass might be unnecessary in the future if Turnstile is disabled in the Clerk dev instance — try the real sign-up first; the Clerk test-mode email convention is `<anything>+clerk_test@example.com` with verification code `424242`.

## Adversarial signal for the roadmap generator

The stub generator (`apps/api/app/services/roadmap_generator.py`) maps `skill_level` to starting phase:

| skill_level   | starting phase | first phase title          |
| ------------- | -------------- | -------------------------- |
| beginner      | 1              | Foundations                |
| intermediate  | 3              | Deep Learning + LLM Basics |
| advanced      | 5              | AI Agents                  |

When verifying the data flow, **submit the assessment with `intermediate` and assert that `/roadmap` renders "Phase 3: Deep Learning + LLM Basics" as the first card** — a static placeholder cannot accidentally produce that string while *also* rendering the rest of the spec-derived phases. This is much stronger than asserting the page just "loads".

## DB regression

```sh
docker exec aieo-postgres psql -U aieo -d aieo -c "SELECT user_id, current_phase, generated_plan->>'summary' AS summary FROM roadmaps WHERE is_active = true;"
```

Expected after submitting `intermediate`: exactly one row, `current_phase = 3`, summary contains `Phase 3` and `intermediate`.

## Quick lint / typecheck / test commands

- API: `cd apps/api && uv run ruff check . && uv run mypy app && uv run pytest`
- Web: `cd apps/web && pnpm lint && pnpm typecheck && pnpm build`
