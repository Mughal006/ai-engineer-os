/** Server-side API client for the FastAPI backend.
 *
 * Forwards the Clerk session token (when configured) to the backend so that
 * `/users/me` and `/roadmaps/*` resolve to the correct user. When Clerk is
 * unconfigured the backend falls back to a deterministic dev user.
 */
import { auth } from "@clerk/nextjs/server";

const API_BASE = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

async function authHeaders(): Promise<HeadersInit> {
  try {
    const { getToken } = await auth();
    const token = await getToken();
    if (token) return { Authorization: `Bearer ${token}` };
  } catch {
    // No Clerk in this environment — fine, the API uses a dev user.
  }
  return {};
}

export type SkillLevel = "beginner" | "intermediate" | "advanced";

export interface SkillAssessment {
  skill_level: SkillLevel;
  target_role: string;
  daily_hours: number;
  deadline?: string | null;
  interests?: string[];
}

export interface RoadmapPhase {
  phase: number;
  title: string;
  duration_weeks: number;
  topics: string[];
  project: string | null;
}

export interface RoadmapTask {
  day: number;
  title: string;
  kind: "lesson" | "exercise" | "quiz" | "project" | "interview" | "revision";
  estimated_minutes: number;
}

export interface RoadmapPlan {
  summary: string;
  phases: RoadmapPhase[];
  daily_tasks: RoadmapTask[];
}

export interface Roadmap {
  id: string;
  user_id: string;
  is_active: boolean;
  current_phase: number;
  completion_percentage: number;
  generated_plan: RoadmapPlan;
  created_at: string;
  updated_at: string;
}

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const headers = {
    "Content-Type": "application/json",
    ...(await authHeaders()),
    ...(init?.headers ?? {})
  };
  const res = await fetch(`${API_BASE}${path}`, {
    ...init,
    headers,
    cache: "no-store"
  });
  if (!res.ok) {
    const text = await res.text();
    throw new Error(`API ${res.status}: ${text}`);
  }
  return (await res.json()) as T;
}

export async function getMyRoadmap(): Promise<Roadmap | null> {
  try {
    return await request<Roadmap>("/roadmaps/me");
  } catch (err) {
    if (err instanceof Error && err.message.startsWith("API 404")) return null;
    throw err;
  }
}

export async function createRoadmap(payload: SkillAssessment): Promise<Roadmap> {
  return request<Roadmap>("/roadmaps", {
    method: "POST",
    body: JSON.stringify(payload)
  });
}

export interface CurriculumTopic {
  slug: string;
  title: string;
  phase: number;
  phase_title: string;
}

export interface Lesson {
  slug: string;
  title: string;
  phase: number;
  phase_title: string;
  beginner_explanation: string;
  advanced_explanation: string;
  worked_example: string;
  key_points: string[];
  estimated_minutes: number;
}

export interface QuizQuestion {
  index: number;
  prompt: string;
  options: string[];
}

export interface Quiz {
  slug: string;
  title: string;
  phase: number;
  phase_title: string;
  passing_score: number;
  questions: QuizQuestion[];
}

export interface QuizQuestionResult {
  index: number;
  correct: boolean;
  correct_index: number;
  explanation: string;
}

export interface QuizResult {
  slug: string;
  score: number;
  passed: boolean;
  passing_score: number;
  mastery_score: number;
  attempts: number;
  per_question: QuizQuestionResult[];
}

export interface ProgressEntry {
  slug: string;
  title: string;
  phase: number;
  phase_title: string;
  completed: boolean;
  mastery_score: number;
  attempts: number;
  last_reviewed: string | null;
}

export interface Progress {
  entries: ProgressEntry[];
  total_topics: number;
  completed_topics: number;
  completion_percentage: number;
}

export async function getLesson(slug: string): Promise<Lesson | null> {
  try {
    return await request<Lesson>(`/topics/${encodeURIComponent(slug)}/lesson`);
  } catch (err) {
    if (err instanceof Error && err.message.startsWith("API 404")) return null;
    throw err;
  }
}

export async function getQuiz(slug: string): Promise<Quiz | null> {
  try {
    return await request<Quiz>(`/quizzes/${encodeURIComponent(slug)}`);
  } catch (err) {
    if (err instanceof Error && err.message.startsWith("API 404")) return null;
    throw err;
  }
}

export async function submitQuiz(slug: string, answers: number[]): Promise<QuizResult> {
  return request<QuizResult>(`/quizzes/${encodeURIComponent(slug)}/submit`, {
    method: "POST",
    body: JSON.stringify({ answers })
  });
}

export async function markLessonComplete(
  slug: string
): Promise<{ slug: string; completed: boolean; mastery_score: number; attempts: number }> {
  return request(`/topics/${encodeURIComponent(slug)}/complete`, { method: "POST" });
}

export async function getMyProgress(): Promise<Progress> {
  return request<Progress>("/progress/me");
}

export interface InterviewTurn {
  role: "assistant" | "user";
  kind: "question" | "answer" | "feedback" | "final";
  content: string;
  index: number;
  score?: number | null;
}

export interface Interview {
  id: string;
  slug: string;
  title: string;
  phase: number;
  phase_title: string;
  transcript: InterviewTurn[];
  question_index: number;
  total_questions: number;
  finished: boolean;
  score: number | null;
  ai_feedback: string | null;
  passing_score: number;
  created_at: string;
}

export interface InterviewListEntry {
  id: string;
  slug: string;
  title: string;
  phase: number;
  phase_title: string;
  finished: boolean;
  score: number | null;
  created_at: string;
}

export async function startInterview(slug: string): Promise<Interview> {
  return request<Interview>("/interviews/start", {
    method: "POST",
    body: JSON.stringify({ slug })
  });
}

export async function postInterviewAnswer(
  interviewId: string,
  answer: string
): Promise<Interview> {
  return request<Interview>(`/interviews/${encodeURIComponent(interviewId)}/answer`, {
    method: "POST",
    body: JSON.stringify({ answer })
  });
}

export async function getInterview(interviewId: string): Promise<Interview | null> {
  try {
    return await request<Interview>(`/interviews/${encodeURIComponent(interviewId)}`);
  } catch (err) {
    if (err instanceof Error && err.message.startsWith("API 404")) return null;
    throw err;
  }
}

export async function listMyInterviews(): Promise<InterviewListEntry[]> {
  const res = await request<{ entries: InterviewListEntry[] }>("/interviews/me");
  return res.entries;
}
