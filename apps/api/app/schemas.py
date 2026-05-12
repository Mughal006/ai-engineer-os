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


class CurriculumTopicOut(BaseModel):
    slug: str
    title: str
    phase: int
    phase_title: str


class LessonOut(BaseModel):
    slug: str
    title: str
    phase: int
    phase_title: str
    beginner_explanation: str
    advanced_explanation: str
    worked_example: str
    key_points: list[str]
    estimated_minutes: int


class QuizQuestionOut(BaseModel):
    index: int
    prompt: str
    options: list[str]


class QuizOut(BaseModel):
    slug: str
    title: str
    phase: int
    phase_title: str
    passing_score: float
    questions: list[QuizQuestionOut]


class QuizSubmitIn(BaseModel):
    answers: list[int] = Field(min_length=1, max_length=20)


class QuizQuestionResult(BaseModel):
    index: int
    correct: bool
    correct_index: int
    explanation: str


class QuizResult(BaseModel):
    slug: str
    score: float
    passed: bool
    passing_score: float
    mastery_score: float
    attempts: int
    per_question: list[QuizQuestionResult]


class ProgressEntry(BaseModel):
    slug: str
    title: str
    phase: int
    phase_title: str
    completed: bool
    mastery_score: float
    attempts: int
    last_reviewed: datetime | None


class ProgressOut(BaseModel):
    entries: list[ProgressEntry]
    total_topics: int
    completed_topics: int
    completion_percentage: float


class LessonCompleteOut(BaseModel):
    slug: str
    completed: bool
    mastery_score: float
    attempts: int
