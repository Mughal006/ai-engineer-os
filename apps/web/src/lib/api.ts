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
