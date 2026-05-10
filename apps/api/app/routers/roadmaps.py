"""Roadmap endpoints."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.auth import get_current_user
from app.db import get_db
from app.models import Roadmap, User
from app.schemas import RoadmapOut, RoadmapPlan, SkillAssessmentIn
from app.services.roadmap_generator import generate_plan

router = APIRouter(prefix="/roadmaps", tags=["roadmaps"])


@router.post("", response_model=RoadmapOut, status_code=status.HTTP_201_CREATED)
def create_roadmap(
    assessment: SkillAssessmentIn,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Roadmap:
    """Generate and persist a personalized roadmap for the current user."""
    plan = generate_plan(assessment)

    # Update profile fields from the assessment.
    current_user.skill_level = assessment.skill_level
    current_user.target_role = assessment.target_role
    current_user.daily_hours = assessment.daily_hours
    current_user.deadline = assessment.deadline

    # Deactivate previous roadmaps.
    db.query(Roadmap).filter(
        Roadmap.user_id == current_user.id, Roadmap.is_active.is_(True)
    ).update({Roadmap.is_active: False})

    roadmap = Roadmap(
        user_id=current_user.id,
        is_active=True,
        current_phase=plan.phases[0].phase if plan.phases else 1,
        completion_percentage=0.0,
        generated_plan=plan.model_dump(),
    )
    db.add(roadmap)
    db.commit()
    db.refresh(roadmap)
    return roadmap


@router.get("/me", response_model=RoadmapOut)
def get_my_roadmap(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Roadmap:
    """Fetch the current user's active roadmap."""
    roadmap = (
        db.query(Roadmap)
        .filter(Roadmap.user_id == current_user.id, Roadmap.is_active.is_(True))
        .order_by(Roadmap.created_at.desc())
        .first()
    )
    if roadmap is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No active roadmap. Submit a skill assessment to generate one.",
        )
    return roadmap


@router.get("/preview", response_model=RoadmapPlan)
def preview_roadmap(assessment: SkillAssessmentIn = Depends()) -> RoadmapPlan:
    """Return a generated plan without persisting it. Useful for previews."""
    return generate_plan(assessment)
