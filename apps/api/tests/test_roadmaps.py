"""Tests for the Roadmap Generator endpoints."""

from __future__ import annotations

from fastapi.testclient import TestClient


def _assessment(skill: str = "beginner") -> dict[str, object]:
    return {
        "skill_level": skill,
        "target_role": "AI Engineer",
        "daily_hours": 2,
        "interests": ["RAG", "Agents"],
    }


def test_generate_roadmap_persists_and_returns_plan(client: TestClient) -> None:
    response = client.post("/roadmaps", json=_assessment())
    assert response.status_code == 201, response.text
    body = response.json()
    assert body["is_active"] is True
    plan = body["generated_plan"]
    assert "summary" in plan
    assert plan["phases"], "Plan should include at least one phase."
    assert plan["daily_tasks"], "Plan should include daily tasks."
    # First phase for a beginner is Foundations (phase=1).
    assert plan["phases"][0]["phase"] == 1


def test_intermediate_user_starts_at_phase_3(client: TestClient) -> None:
    response = client.post("/roadmaps", json=_assessment(skill="intermediate"))
    assert response.status_code == 201, response.text
    plan = response.json()["generated_plan"]
    assert plan["phases"][0]["phase"] == 3


def test_get_my_roadmap_returns_latest_active(client: TestClient) -> None:
    client.post("/roadmaps", json=_assessment())
    second = client.post("/roadmaps", json=_assessment(skill="advanced"))
    assert second.status_code == 201

    response = client.get("/roadmaps/me")
    assert response.status_code == 200
    body = response.json()
    assert body["is_active"] is True
    assert body["generated_plan"]["phases"][0]["phase"] == 5


def test_get_my_roadmap_404_when_none(client: TestClient) -> None:
    response = client.get("/roadmaps/me")
    assert response.status_code == 404


def test_users_me_creates_dev_user(client: TestClient) -> None:
    response = client.get("/users/me")
    assert response.status_code == 200
    body = response.json()
    assert body["clerk_id"] == "dev-user"
    assert body["email"] == "dev@example.com"
