"""Pytest fixtures: spin up an in-process SQLite DB and a TestClient."""

from __future__ import annotations

import os
from collections.abc import Generator

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool


@pytest.fixture(scope="session", autouse=True)
def _set_env() -> None:
    # Ensure auth is disabled for tests (dev-user mode).
    os.environ.pop("CLERK_SECRET_KEY", None)
    os.environ.pop("CLERK_JWT_ISSUER", None)


@pytest.fixture()
def client() -> Generator[TestClient, None, None]:
    """A TestClient backed by a fresh in-memory SQLite database.

    SQLite is fine for unit tests of the schema/routes; the JSON columns map
    to TEXT and UUID maps to a 32-char string when using SQLAlchemy with
    SQLite, which is enough to exercise our handlers.
    """
    from app import db as db_module
    from app import models  # noqa: F401  ensure models register on Base
    from app.db import Base, get_db
    from app.main import app

    test_engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    TestSession = sessionmaker(bind=test_engine, autoflush=False, autocommit=False, future=True)
    Base.metadata.create_all(bind=test_engine)

    # Patch the global session factory so app code (e.g. auth bootstrap) uses
    # the test engine too.
    db_module.engine = test_engine
    db_module.SessionLocal = TestSession

    def override_get_db() -> Generator[Session, None, None]:
        session = TestSession()
        try:
            yield session
        finally:
            session.close()

    app.dependency_overrides[get_db] = override_get_db
    try:
        with TestClient(app) as test_client:
            yield test_client
    finally:
        app.dependency_overrides.clear()
        Base.metadata.drop_all(bind=test_engine)
