"use client";

import { useState } from "react";
import type { Lesson } from "@/lib/api";

const TABS = [
  { id: "beginner", label: "Beginner" },
  { id: "advanced", label: "Advanced" },
  { id: "example", label: "Worked example" }
] as const;

type TabId = (typeof TABS)[number]["id"];

export function LessonView({ lesson }: { lesson: Lesson }) {
  const [tab, setTab] = useState<TabId>("beginner");

  const body =
    tab === "beginner"
      ? lesson.beginner_explanation
      : tab === "advanced"
        ? lesson.advanced_explanation
        : lesson.worked_example;

  return (
    <div className="space-y-6 rounded-lg border border-border p-6">
      <div className="flex gap-2 border-b border-border">
        {TABS.map((t) => (
          <button
            type="button"
            key={t.id}
            onClick={() => setTab(t.id)}
            className={
              "border-b-2 px-3 py-2 text-sm " +
              (tab === t.id
                ? "border-primary font-medium text-foreground"
                : "border-transparent text-muted-foreground hover:text-foreground")
            }
          >
            {t.label}
          </button>
        ))}
      </div>
      <p className="text-base leading-relaxed">{body}</p>
      <div>
        <h3 className="font-semibold">Key points</h3>
        <ul className="mt-2 list-disc space-y-1 pl-5 text-sm">
          {lesson.key_points.map((p, i) => (
            <li key={i}>{p}</li>
          ))}
        </ul>
      </div>
    </div>
  );
}
