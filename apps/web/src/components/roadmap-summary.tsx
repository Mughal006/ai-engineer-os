import Link from "next/link";
import type { Roadmap } from "@/lib/api";

const KIND_BADGE: Record<string, string> = {
  lesson: "bg-blue-100 text-blue-900",
  exercise: "bg-emerald-100 text-emerald-900",
  quiz: "bg-amber-100 text-amber-900",
  project: "bg-purple-100 text-purple-900",
  interview: "bg-rose-100 text-rose-900",
  revision: "bg-slate-100 text-slate-900"
};

export function RoadmapSummary({ roadmap }: { roadmap: Roadmap }) {
  const plan = roadmap.generated_plan;
  const today = plan.daily_tasks.filter((t) => t.day === 1);

  return (
    <div className="grid gap-6 md:grid-cols-3">
      <div className="md:col-span-2 space-y-4 rounded-lg border border-border p-6">
        <div>
          <h2 className="text-xl font-semibold">Today&apos;s plan</h2>
          <p className="text-sm text-muted-foreground">{plan.summary}</p>
        </div>
        <ul className="divide-y divide-border">
          {today.map((task, i) => (
            <li key={i} className="flex items-center justify-between py-3">
              <div className="flex items-center gap-3">
                <span
                  className={
                    "inline-block rounded px-2 py-0.5 text-xs font-medium " +
                    (KIND_BADGE[task.kind] ?? "bg-slate-100 text-slate-900")
                  }
                >
                  {task.kind}
                </span>
                <span className="text-sm">{task.title}</span>
              </div>
              <span className="text-xs text-muted-foreground">{task.estimated_minutes} min</span>
            </li>
          ))}
        </ul>
        <Link href="/roadmap" className="text-sm text-primary underline-offset-4 hover:underline">
          View full roadmap →
        </Link>
      </div>

      <div className="space-y-4 rounded-lg border border-border p-6">
        <h3 className="font-semibold">Progress</h3>
        <div>
          <div className="text-3xl font-semibold">
            {Math.round(roadmap.completion_percentage)}%
          </div>
          <div className="text-sm text-muted-foreground">Plan completion</div>
        </div>
        <div>
          <div className="text-3xl font-semibold">Phase {roadmap.current_phase}</div>
          <div className="text-sm text-muted-foreground">
            {plan.phases.find((p) => p.phase === roadmap.current_phase)?.title ?? "—"}
          </div>
        </div>
        <div>
          <div className="text-3xl font-semibold">{plan.phases.length}</div>
          <div className="text-sm text-muted-foreground">Phases ahead</div>
        </div>
      </div>
    </div>
  );
}
