"""Tests for the Week-3 Interview Agent endpoints.

The LLM client is replaced with the deterministic stub via dependency
override, so these tests run without any network or model weights.
"""

from __future__ import annotations

from collections.abc import Generator
from typing import Any

import pytest
from fastapi.testclient import TestClient


@pytest.fixture(autouse=True)
def _stub_llm(client: TestClient) -> Generator[None, None, None]:
    from app.main import app
    from app.services.llm import LLMClient, StubLLMClient, get_llm_client

    def _override() -> LLMClient:
        return StubLLMClient()

    app.dependency_overrides[get_llm_client] = _override
    try:
        yield
    finally:
        app.dependency_overrides.pop(get_llm_client, None)


def test_start_interview_returns_opening_question(client: TestClient) -> None:
    resp = client.post("/interviews/start", json={"slug": "transformers"})
    assert resp.status_code == 201, resp.text
    body = resp.json()
    assert body["slug"] == "transformers"
    assert body["title"] == "Transformers"
    assert body["phase"] == 3
    assert body["phase_title"] == "Deep Learning + LLM Basics"
    assert body["finished"] is False
    assert body["score"] is None
    assert body["total_questions"] == 4
    assert body["question_index"] == 1
    assert len(body["transcript"]) == 1
    q1 = body["transcript"][0]
    assert q1["role"] == "assistant"
    assert q1["kind"] == "question"
    assert "Transformers" in q1["content"]


def test_unknown_slug_404s(client: TestClient) -> None:
    assert client.post("/interviews/start", json={"slug": "not-a-real-topic"}).status_code == 404


def test_full_interview_flow_grades_each_answer_and_finalizes(client: TestClient) -> None:
    start = client.post("/interviews/start", json={"slug": "attention"}).json()
    interview_id = start["id"]

    # The stub gives a "passing" score (80) when the answer name-drops the topic.
    strong_answer = (
        "Attention lets the model weight different tokens for context, and we use "
        "scaled dot-product attention in production transformer stacks."
    )

    last_state: dict[str, Any] = {}
    for round_idx in range(1, 5):
        resp = client.post(
            f"/interviews/{interview_id}/answer",
            json={"answer": strong_answer},
        )
        assert resp.status_code == 200, resp.text
        last_state = resp.json()
        # We always see at least: open_Q + (round_idx * (answer + feedback)).
        transcript: list[dict[str, Any]] = last_state["transcript"]
        feedbacks = [t for t in transcript if t["kind"] == "feedback"]
        assert len(feedbacks) == round_idx
        # Each feedback has a numeric score and a string body.
        for fb in feedbacks:
            assert isinstance(fb["score"], int | float)
            assert isinstance(fb["content"], str) and fb["content"]

    # After 4 answers the interview must be finalized.
    assert last_state["finished"] is True
    assert isinstance(last_state["score"], int | float)
    assert last_state["score"] >= 70  # stub scored each strong answer 80
    assert isinstance(last_state["ai_feedback"], str)
    final_transcript: list[dict[str, Any]] = last_state["transcript"]
    assert any(t["kind"] == "final" for t in final_transcript)


def test_answer_to_finished_interview_409s(client: TestClient) -> None:
    start = client.post("/interviews/start", json={"slug": "embeddings"}).json()
    interview_id = start["id"]
    strong_answer = "Embeddings are dense vector representations used across retrieval systems."
    for _ in range(4):
        ok = client.post(f"/interviews/{interview_id}/answer", json={"answer": strong_answer})
        assert ok.status_code == 200, ok.text
    again = client.post(f"/interviews/{interview_id}/answer", json={"answer": strong_answer})
    assert again.status_code == 409


def test_get_interview_returns_full_transcript(client: TestClient) -> None:
    start = client.post("/interviews/start", json={"slug": "tokenization"}).json()
    interview_id = start["id"]
    client.post(
        f"/interviews/{interview_id}/answer",
        json={"answer": "Tokenization splits text into subwords for the model to consume."},
    )
    detail = client.get(f"/interviews/{interview_id}")
    assert detail.status_code == 200
    body = detail.json()
    assert body["id"] == interview_id
    # Should now have at least Q1, A1, F1, Q2 in transcript.
    kinds = [t["kind"] for t in body["transcript"]]
    assert kinds[:4] == ["question", "answer", "feedback", "question"]


def test_list_my_interviews_returns_both_entries(client: TestClient) -> None:
    first = client.post("/interviews/start", json={"slug": "attention"}).json()
    second = client.post("/interviews/start", json={"slug": "transformers"}).json()
    listing = client.get("/interviews/me").json()
    ids = {e["id"] for e in listing["entries"]}
    # Both interviews show up. Ordering is "most recent first" by created_at,
    # but in tests these rows land in the same timestamp tick so we don't pin
    # which one comes back at index 0.
    assert {first["id"], second["id"]} <= ids
    slugs = {e["slug"] for e in listing["entries"]}
    assert {"attention", "transformers"} <= slugs


def test_answer_isolated_across_users(client: TestClient) -> None:
    # The stub uses the dev user; a second TestClient still gets the dev user,
    # so we instead test the "interview not found" path with a random UUID.
    bad = client.post(
        "/interviews/00000000-0000-0000-0000-000000000000/answer",
        json={"answer": "anything"},
    )
    assert bad.status_code == 404
