"use server";

import { createRoadmap, type SkillAssessment } from "@/lib/api";

export type GenerateRoadmapResult = { ok: true } | { ok: false; error: string };

export async function generateRoadmap(payload: SkillAssessment): Promise<GenerateRoadmapResult> {
  try {
    await createRoadmap(payload);
    return { ok: true };
  } catch (err) {
    const message = err instanceof Error ? err.message : "Failed to generate roadmap.";
    return { ok: false, error: message };
  }
}
