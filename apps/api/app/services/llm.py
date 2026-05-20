"""LLM client abstraction.

Two implementations live here:

* :class:`OllamaClient` — calls a local Ollama server (the default for dev).
* :class:`StubLLMClient` — deterministic, used in tests so CI does not need
  network or model weights.

Agent code (interview agent, future tutor agent) depends on the protocol, not
on the concrete provider. The provider is wired through the FastAPI dependency
:func:`get_llm_client`, so tests can override it via ``app.dependency_overrides``.
"""

from __future__ import annotations

import json
import logging
from typing import Protocol

import httpx
from fastapi import Depends

from app.config import Settings, get_settings

logger = logging.getLogger(__name__)


class ChatMessage(dict[str, str]):
    """Tiny typed wrapper so we get autocomplete on role/content keys."""


def msg(role: str, content: str) -> dict[str, str]:
    return {"role": role, "content": content}


class LLMClient(Protocol):
    """Minimal chat interface every backend has to implement."""

    def chat(
        self,
        messages: list[dict[str, str]],
        *,
        json_mode: bool = False,
        temperature: float = 0.4,
    ) -> str: ...


class OllamaClient:
    """Synchronous client for the Ollama ``/api/chat`` endpoint."""

    def __init__(self, base_url: str, model: str, timeout_seconds: float = 120.0) -> None:
        self._base_url = base_url.rstrip("/")
        self._model = model
        self._timeout = timeout_seconds

    def chat(
        self,
        messages: list[dict[str, str]],
        *,
        json_mode: bool = False,
        temperature: float = 0.4,
    ) -> str:
        payload: dict[str, object] = {
            "model": self._model,
            "messages": messages,
            "stream": False,
            "options": {"temperature": temperature},
        }
        if json_mode:
            payload["format"] = "json"
        try:
            with httpx.Client(timeout=self._timeout) as http:
                resp = http.post(f"{self._base_url}/api/chat", json=payload)
                resp.raise_for_status()
                body = resp.json()
        except httpx.HTTPError as exc:
            logger.warning("Ollama call failed (%s); falling back to stub.", exc)
            return StubLLMClient().chat(messages, json_mode=json_mode, temperature=temperature)
        content = body.get("message", {}).get("content")
        if not isinstance(content, str):
            logger.warning("Ollama returned unexpected payload: %r", body)
            return StubLLMClient().chat(messages, json_mode=json_mode, temperature=temperature)
        return content


class StubLLMClient:
    """Deterministic LLM stub used in tests and as an Ollama fallback.

    The output is keyed off the **system prompt**: the interview agent tags
    every call with a distinctive role marker (``[INTERVIEW_QUESTION]``,
    ``[INTERVIEW_GRADE]``, ``[INTERVIEW_FINAL]``) so this stub can return a
    shape the caller expects without parsing free-form text.
    """

    def chat(
        self,
        messages: list[dict[str, str]],
        *,
        json_mode: bool = False,
        temperature: float = 0.4,
    ) -> str:
        del temperature
        joined = "\n".join(m.get("content", "") for m in messages)
        if "[INTERVIEW_QUESTION]" in joined:
            topic = _between(joined, "<topic>", "</topic>") or "the topic"
            index = _between(joined, "<index>", "</index>") or "1"
            return (
                f"Question {index}: In your own words, can you walk me through how "
                f"{topic} works and where you would use it in a production AI system?"
            )
        if "[INTERVIEW_GRADE]" in joined:
            topic = _between(joined, "<topic>", "</topic>") or "the topic"
            answer = _between(joined, "<answer>", "</answer>") or ""
            # Heuristic: if the answer references the topic and is non-trivial,
            # award a passing score. Otherwise low.
            score = 80 if topic.lower() in answer.lower() and len(answer) > 30 else 30
            payload = {
                "score": score,
                "feedback": (
                    "Solid grounding in the core idea — push deeper on production trade-offs."
                    if score >= 70
                    else "Try to connect the concept back to a concrete engineering scenario."
                ),
            }
            return json.dumps(payload) if json_mode else json.dumps(payload)
        if "[INTERVIEW_FINAL]" in joined:
            payload = {
                "score": 70,
                "feedback": (
                    "Overall a passable answer set. Tighten the production-grounded answers "
                    "and you'll be interview-ready on this topic."
                ),
            }
            return json.dumps(payload) if json_mode else json.dumps(payload)
        return "OK"


def _between(text: str, start: str, end: str) -> str | None:
    s = text.find(start)
    if s < 0:
        return None
    e = text.find(end, s + len(start))
    if e < 0:
        return None
    return text[s + len(start) : e].strip()


def get_llm_client(settings: Settings = Depends(get_settings)) -> LLMClient:
    """FastAPI dependency. Override in tests via ``app.dependency_overrides``."""
    if settings.llm_provider == "stub":
        return StubLLMClient()
    return OllamaClient(
        base_url=settings.ollama_base_url,
        model=settings.llm_model,
        timeout_seconds=settings.llm_timeout_seconds,
    )
