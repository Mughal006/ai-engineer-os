"""Roadmap Generator agent.

Produces a deterministic, structured roadmap from a skill assessment.
When `OPENAI_API_KEY` is set, this is where a LangChain/OpenAI call would
be wired in — for the MVP we ship a deterministic stub that mirrors the
curriculum from §5 of the product spec, so the rest of the system can
be built and tested without LLM calls.
"""

from __future__ import annotations

from app.schemas import RoadmapPhase, RoadmapPlan, RoadmapTask, SkillAssessmentIn

CURRICULUM: list[RoadmapPhase] = [
    RoadmapPhase(
        phase=1,
        title="Foundations",
        duration_weeks=2,
        topics=["Python", "OOP", "Data Structures", "APIs", "Git/GitHub", "Linux", "SQL", "HTTP"],
        project="Build a CLI automation tool",
    ),
    RoadmapPhase(
        phase=2,
        title="ML Foundations",
        duration_weeks=2,
        topics=[
            "NumPy",
            "Pandas",
            "Matplotlib",
            "ML basics",
            "Supervised learning",
            "Regression",
            "Classification",
            "Evaluation metrics",
        ],
        project="Customer churn prediction",
    ),
    RoadmapPhase(
        phase=3,
        title="Deep Learning + LLM Basics",
        duration_weeks=2,
        topics=[
            "Neural networks",
            "Transformers",
            "Embeddings",
            "Tokenization",
            "Attention",
            "HuggingFace",
            "Inference",
        ],
        project="Build a text classifier with HuggingFace",
    ),
    RoadmapPhase(
        phase=4,
        title="RAG + Vector Databases",
        duration_weeks=2,
        topics=["Embeddings", "Chunking", "Retrieval", "Vector DBs", "Semantic search"],
        project="PDF chatbot with RAG",
    ),
    RoadmapPhase(
        phase=5,
        title="AI Agents",
        duration_weeks=2,
        topics=["Tool calling", "Memory", "Planning", "Workflows", "Multi-agent systems"],
        project="Autonomous research assistant",
    ),
    RoadmapPhase(
        phase=6,
        title="Production AI Engineering",
        duration_weeks=2,
        topics=[
            "FastAPI",
            "Docker",
            "Deployment",
            "Monitoring",
            "Scaling",
            "Evaluation",
            "Caching",
        ],
        project="Deploy an AI SaaS MVP",
    ),
    RoadmapPhase(
        phase=7,
        title="Interview + Placement Mode",
        duration_weeks=2,
        topics=[
            "System design",
            "Resume prep",
            "DSA for AI interviews",
            "Behavioral interviews",
            "Coding interviews",
            "Mock placements",
        ],
        project="Mock placement series",
    ),
]

_STARTING_PHASE_BY_SKILL = {
    "beginner": 1,
    "intermediate": 3,
    "advanced": 5,
}


def _daily_tasks_for(phases: list[RoadmapPhase], daily_hours: float) -> list[RoadmapTask]:
    """Generate the first ~14 days of tasks across the active phases."""
    minutes_per_day = max(30, int(daily_hours * 60))
    tasks: list[RoadmapTask] = []
    day = 1
    for phase in phases[:2]:
        for topic in phase.topics:
            tasks.append(
                RoadmapTask(
                    day=day,
                    title=f"{phase.title}: {topic}",
                    kind="lesson",
                    estimated_minutes=min(45, minutes_per_day // 2),
                )
            )
            tasks.append(
                RoadmapTask(
                    day=day,
                    title=f"{topic} — practice exercise",
                    kind="exercise",
                    estimated_minutes=min(45, minutes_per_day // 2),
                )
            )
            day += 1
            if day > 14:
                return tasks
        if phase.project:
            tasks.append(
                RoadmapTask(
                    day=day,
                    title=f"Project: {phase.project}",
                    kind="project",
                    estimated_minutes=minutes_per_day,
                )
            )
            day += 1
    return tasks


def generate_plan(assessment: SkillAssessmentIn) -> RoadmapPlan:
    """Return a structured plan tailored to the user's assessment.

    The current implementation is deterministic. Swap this for an LLM-backed
    chain (LangChain/LangGraph) once `OPENAI_API_KEY` is provisioned.
    """
    starting_phase = _STARTING_PHASE_BY_SKILL.get(assessment.skill_level.value, 1)
    active_phases = [p for p in CURRICULUM if p.phase >= starting_phase]
    summary = (
        f"Personalized AI Engineer roadmap for a {assessment.skill_level.value} learner "
        f"targeting '{assessment.target_role}'. Plan assumes {assessment.daily_hours}h/day "
        f"and starts at Phase {starting_phase}."
    )
    return RoadmapPlan(
        summary=summary,
        phases=active_phases,
        daily_tasks=_daily_tasks_for(active_phases, assessment.daily_hours),
    )
