"""Curriculum index — single source of truth for topic slugs.

Roadmap phases (from the product spec §5) are defined in
``roadmap_generator.CURRICULUM``. This module derives a flat slug-indexed view
so lesson / quiz / progress endpoints can address each topic by a stable URL
slug independently of how the roadmap is rendered.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from functools import lru_cache

from app.services.roadmap_generator import CURRICULUM


@dataclass(frozen=True)
class CurriculumTopic:
    """A single topic in the curriculum, addressable by its slug."""

    slug: str
    title: str
    phase: int
    phase_title: str


_SLUG_RE = re.compile(r"[^a-z0-9]+")


def slugify(value: str) -> str:
    """Lowercase, hyphenated slug. Stable across runs (used as URL identifier)."""
    return _SLUG_RE.sub("-", value.lower()).strip("-")


@lru_cache(maxsize=1)
def topics_index() -> dict[str, CurriculumTopic]:
    """Return a {slug: CurriculumTopic} mapping covering every topic in the spec.

    When two phases mention the same topic (e.g. "Embeddings" appears in both
    Phase 3 and Phase 4), the slug is disambiguated with the phase number so
    each is independently trackable.
    """
    out: dict[str, CurriculumTopic] = {}
    for phase in CURRICULUM:
        for topic in phase.topics:
            base = slugify(topic)
            slug = base if base not in out else f"{base}-p{phase.phase}"
            out[slug] = CurriculumTopic(
                slug=slug,
                title=topic,
                phase=phase.phase,
                phase_title=phase.title,
            )
    return out


def slug_for(phase: int, topic_title: str) -> str:
    """Resolve the slug for a (phase, topic_title) pair from the curriculum."""
    target_base = slugify(topic_title)
    for slug, t in topics_index().items():
        if t.phase == phase and slugify(t.title) == target_base:
            return slug
    return target_base


def get_topic(slug: str) -> CurriculumTopic | None:
    return topics_index().get(slug)
