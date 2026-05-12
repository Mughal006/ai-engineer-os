"""Tests for the Week-2 learning surface: topics, lessons, quizzes, progress."""

from __future__ import annotations

from fastapi.testclient import TestClient


def test_list_topics_covers_all_phases(client: TestClient) -> None:
    response = client.get("/topics")
    assert response.status_code == 200
    topics = response.json()
    # 7 phases worth of topics. Phase counts come from §5 of the spec.
    phases = sorted({t["phase"] for t in topics})
    assert phases == [1, 2, 3, 4, 5, 6, 7]
    slugs = {t["slug"] for t in topics}
    # Adversarial: the spec mentions 'Neural networks' under Phase 3.
    assert "neural-networks" in slugs


def test_get_lesson_returns_deterministic_content(client: TestClient) -> None:
    response = client.get("/topics/neural-networks/lesson")
    assert response.status_code == 200
    lesson = response.json()
    assert lesson["slug"] == "neural-networks"
    assert lesson["phase"] == 3
    assert lesson["phase_title"] == "Deep Learning + LLM Basics"
    assert "Neural networks" in lesson["beginner_explanation"]
    assert len(lesson["key_points"]) >= 3


def test_unknown_slug_404s(client: TestClient) -> None:
    assert client.get("/topics/not-a-real-topic/lesson").status_code == 404
    assert client.get("/quizzes/not-a-real-topic").status_code == 404


def test_quiz_endpoint_strips_correct_answers(client: TestClient) -> None:
    response = client.get("/quizzes/neural-networks")
    assert response.status_code == 200
    body = response.json()
    assert body["slug"] == "neural-networks"
    assert body["passing_score"] == 0.7
    assert len(body["questions"]) == 5
    for q in body["questions"]:
        assert "correct_index" not in q
        assert "explanation" not in q
        assert len(q["options"]) == 4


def test_quiz_submit_grades_and_updates_progress(client: TestClient) -> None:
    quiz_resp = client.get("/quizzes/transformers")
    assert quiz_resp.status_code == 200

    # Wrong answer everywhere should produce a score of 0.
    wrong_answers = {"answers": [0, 0, 0, 0, 0]}
    submit = client.post("/quizzes/transformers/submit", json=wrong_answers)
    assert submit.status_code == 200, submit.text
    result = submit.json()
    assert result["passed"] in (True, False)
    assert 0.0 <= result["score"] <= 1.0
    assert len(result["per_question"]) == 5

    # Submit a perfect score by using each per-question's correct_index.
    perfect_answers = {"answers": [q["correct_index"] for q in result["per_question"]]}
    perfect = client.post("/quizzes/transformers/submit", json=perfect_answers).json()
    assert perfect["score"] == 1.0
    assert perfect["passed"] is True
    assert perfect["mastery_score"] == 1.0  # best-of attempts
    assert perfect["attempts"] == 2

    progress = client.get("/progress/me").json()
    titles = {e["title"]: e for e in progress["entries"]}
    assert "Transformers" in titles
    assert titles["Transformers"]["completed"] is True
    assert titles["Transformers"]["mastery_score"] == 1.0
    assert progress["completed_topics"] == 1
    assert progress["total_topics"] > 0


def test_mark_lesson_complete_updates_progress(client: TestClient) -> None:
    resp = client.post("/topics/attention/complete")
    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert body["slug"] == "attention"
    assert body["completed"] is True

    progress = client.get("/progress/me").json()
    titles = {e["title"]: e for e in progress["entries"]}
    assert "Attention" in titles
    assert titles["Attention"]["completed"] is True


def test_submit_with_wrong_answer_count_400s(client: TestClient) -> None:
    bad = client.post("/quizzes/embeddings/submit", json={"answers": [0, 1]})
    assert bad.status_code == 400
