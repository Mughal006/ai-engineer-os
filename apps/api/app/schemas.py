"""Pydantic schemas for request/response payloads."""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, EmailStr, Field

from app.models import SkillLevel


class UserOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    clerk_id: str
    email: EmailStr
    name: str | None = None
    skill_level: SkillLevel | None = None
    target_role: str | None = None
    daily_hours: float | None = None
    deadline: datetime | None = None
    created_at: datetime


class SkillAssessmentIn(BaseModel):
    """Input for the Roadmap Generator."""

    skill_level: SkillLevel
    target_role: str = Field(min_length=2, max_length=120)
    daily_hours: float = Field(gt=0, le=24)
    deadline: datetime | None = None
    interests: list[str] = Field(default_factory=list)


class RoadmapTask(BaseModel):
    day: int
    title: str
    kind: Literal["lesson", "exercise", "quiz", "project", "interview", "revision"]
    estimated_minutes: int


class RoadmapPhase(BaseModel):
    phase: int
    title: str
    duration_weeks: int
    topics: list[str]
    project: str | None = None


class RoadmapPlan(BaseModel):
    summary: str
    phases: list[RoadmapPhase]
    daily_tasks: list[RoadmapTask]


class RoadmapOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    user_id: uuid.UUID
    is_active: bool
    current_phase: int
    completion_percentage: float
    generated_plan: RoadmapPlan
    created_at: datetime
    updated_at: datetime
