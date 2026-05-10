"use client";

import { useRouter } from "next/navigation";
import { useState, useTransition } from "react";

import type { SkillLevel } from "@/lib/api";
import { generateRoadmap } from "./assessment-action";

const LEVELS: { value: SkillLevel; label: string; helper: string }[] = [
  { value: "beginner", label: "Beginner", helper: "New to coding or just starting Python." },
  {
    value: "intermediate",
    label: "Intermediate",
    helper: "Comfortable with Python and a bit of ML."
  },
  { value: "advanced", label: "Advanced", helper: "Already shipping ML/LLM features." }
];

export function AssessmentForm() {
  const router = useRouter();
  const [pending, startTransition] = useTransition();
  const [error, setError] = useState<string | null>(null);
  const [skillLevel, setSkillLevel] = useState<SkillLevel>("beginner");
  const [targetRole, setTargetRole] = useState("AI Engineer");
  const [dailyHours, setDailyHours] = useState(2);
  const [interests, setInterests] = useState("RAG, Agents");

  function onSubmit(e: React.FormEvent) {
    e.preventDefault();
    setError(null);
    startTransition(async () => {
      const result = await generateRoadmap({
        skill_level: skillLevel,
        target_role: targetRole,
        daily_hours: dailyHours,
        interests: interests
          .split(",")
          .map((s) => s.trim())
          .filter(Boolean)
      });
      if (result.ok) {
        router.push("/roadmap");
      } else {
        setError(result.error);
      }
    });
  }

  return (
    <form onSubmit={onSubmit} className="space-y-6 rounded-lg border border-border p-6">
      <div className="space-y-2">
        <label className="text-sm font-medium">Current skill level</label>
        <div className="grid gap-2 md:grid-cols-3">
          {LEVELS.map((l) => {
            const selected = skillLevel === l.value;
            return (
              <button
                key={l.value}
                type="button"
                onClick={() => setSkillLevel(l.value)}
                className={
                  "rounded-md border p-3 text-left text-sm transition " +
                  (selected
                    ? "border-primary bg-accent"
                    : "border-border hover:border-foreground/30")
                }
              >
                <div className="font-medium">{l.label}</div>
                <div className="text-xs text-muted-foreground">{l.helper}</div>
              </button>
            );
          })}
        </div>
      </div>

      <div className="space-y-2">
        <label htmlFor="target_role" className="text-sm font-medium">
          Target role
        </label>
        <input
          id="target_role"
          value={targetRole}
          onChange={(e) => setTargetRole(e.target.value)}
          required
          maxLength={120}
          className="w-full rounded-md border border-border bg-background px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-primary/30"
        />
      </div>

      <div className="space-y-2">
        <label htmlFor="daily_hours" className="text-sm font-medium">
          Daily study hours
        </label>
        <input
          id="daily_hours"
          type="number"
          min={0.5}
          max={12}
          step={0.5}
          value={dailyHours}
          onChange={(e) => setDailyHours(Number(e.target.value))}
          required
          className="w-full rounded-md border border-border bg-background px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-primary/30"
        />
      </div>

      <div className="space-y-2">
        <label htmlFor="interests" className="text-sm font-medium">
          Interests (comma-separated)
        </label>
        <input
          id="interests"
          value={interests}
          onChange={(e) => setInterests(e.target.value)}
          placeholder="RAG, Agents, Computer Vision"
          className="w-full rounded-md border border-border bg-background px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-primary/30"
        />
      </div>

      {error ? <p className="text-sm text-red-600">{error}</p> : null}

      <button
        type="submit"
        disabled={pending}
        className="rounded-md bg-primary px-5 py-2.5 text-primary-foreground hover:opacity-90 disabled:opacity-50"
      >
        {pending ? "Generating roadmap…" : "Generate my roadmap"}
      </button>
    </form>
  );
}
