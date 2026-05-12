import Link from "next/link";
import type { Roadmap, RoadmapTask } from "@/lib/api";

function slugify(value: string): string {
  return value
    .toLowerCase()
    .replace(/[^a-z0-9]+/g, "-")
    .replace(/^-+|-+$/g, "");
}

function topicSlug(phase: number, topic: string, seenBaseSlugs: Set<string>): string {
  // Mirror app/services/curriculum.py: duplicate base slugs across phases are
  // disambiguated with -p{phase}. Caller maintains seenBaseSlugs across the
  // whole roadmap render so we get the same slugs the backend computes.
  const base = slugify(topic);
  if (!seenBaseSlugs.has(base)) {
    seenBaseSlugs.add(base);
    return base;
  }
  return `${base}-p${phase}`;
}

const KIND_BADGE: Record<string, string> = {
  lesson: "bg-blue-100 text-blue-900",
  exercise: "bg-emerald-100 text-emerald-900",
  quiz: "bg-amber-100 text-amber-900",
  project: "bg-purple-100 text-purple-900",
  interview: "bg-rose-100 text-rose-900",
  revision: "bg-slate-100 text-slate-900"
};

function tasksByDay(tasks: RoadmapTask[]): Map<number, RoadmapTask[]> {
  const out = new Map<number, RoadmapTask[]>();
  for (const t of tasks) {
    const list = out.get(t.day) ?? [];
    list.push(t);
    out.set(t.day, list);
  }
  return out;
}

export function RoadmapView({ roadmap }: { roadmap: Roadmap }) {
  const plan = roadmap.generated_plan;
  const days = tasksByDay(plan.daily_tasks);
  const sortedDays = Array.from(days.keys()).sort((a, b) => a - b);
  const seenBaseSlugs = new Set<string>();

  return (
    <div className="space-y-10">
      <header>
        <h1 className="text-3xl font-semibold">Your roadmap</h1>
        <p className="mt-1 text-muted-foreground">{plan.summary}</p>
      </header>

      <section className="space-y-4">
        <h2 className="text-xl font-semibold">Phases</h2>
        <div className="grid gap-4 md:grid-cols-2">
          {plan.phases.map((phase) => (
            <div
              key={phase.phase}
              className={
                "rounded-lg border p-5 " +
                (phase.phase === roadmap.current_phase
                  ? "border-primary bg-accent"
                  : "border-border")
              }
            >
              <div className="flex items-baseline justify-between">
                <h3 className="text-lg font-semibold">
                  Phase {phase.phase}: {phase.title}
                </h3>
                <span className="text-xs text-muted-foreground">
                  {phase.duration_weeks} weeks
                </span>
              </div>
              <ul className="mt-3 flex flex-wrap gap-2">
                {phase.topics.map((t) => {
                  const slug = topicSlug(phase.phase, t, seenBaseSlugs);
                  return (
                    <li key={t}>
                      <Link
                        href={`/learn/${slug}`}
                        className="inline-block rounded-full border border-border px-2.5 py-0.5 text-xs hover:bg-accent"
                      >
                        {t}
                      </Link>
                    </li>
                  );
                })}
              </ul>
              {phase.project ? (
                <p className="mt-3 text-sm">
                  <span className="font-medium">Project:</span> {phase.project}
                </p>
              ) : null}
            </div>
          ))}
        </div>
      </section>

      <section className="space-y-4">
        <h2 className="text-xl font-semibold">First two weeks of daily tasks</h2>
        <div className="space-y-4">
          {sortedDays.map((day) => (
            <div key={day} className="rounded-lg border border-border p-4">
              <div className="mb-3 flex items-baseline justify-between">
                <h3 className="font-medium">Day {day}</h3>
                <span className="text-xs text-muted-foreground">
                  {(days.get(day) ?? []).reduce((sum, t) => sum + t.estimated_minutes, 0)} min
                </span>
              </div>
              <ul className="divide-y divide-border">
                {(days.get(day) ?? []).map((task, i) => (
                  <li key={i} className="flex items-center justify-between py-2">
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
                    <span className="text-xs text-muted-foreground">
                      {task.estimated_minutes} min
                    </span>
                  </li>
                ))}
              </ul>
            </div>
          ))}
        </div>
      </section>
    </div>
  );
}
