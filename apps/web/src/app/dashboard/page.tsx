import Link from "next/link";
import { getMyProgress, getMyRoadmap } from "@/lib/api";
import { RoadmapSummary } from "@/components/roadmap-summary";

export const dynamic = "force-dynamic";

export default async function DashboardPage() {
  const [roadmap, progress] = await Promise.all([
    getMyRoadmap().catch(() => null),
    getMyProgress().catch(() => null)
  ]);

  const recent = (progress?.entries ?? [])
    .filter((e) => e.last_reviewed)
    .sort((a, b) => (b.last_reviewed ?? "").localeCompare(a.last_reviewed ?? ""))
    .slice(0, 5);

  return (
    <div className="space-y-8">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-semibold">Dashboard</h1>
          <p className="text-muted-foreground">Your AI engineering progress at a glance.</p>
        </div>
        <Link
          href="/onboarding"
          className="rounded-md border border-border px-4 py-2 text-sm hover:bg-accent"
        >
          {roadmap ? "Regenerate roadmap" : "Take skill assessment"}
        </Link>
      </div>

      {roadmap ? (
        <RoadmapSummary roadmap={roadmap} progress={progress} />
      ) : (
        <div className="rounded-lg border border-dashed border-border p-10 text-center">
          <h2 className="text-xl font-medium">You don&apos;t have a roadmap yet.</h2>
          <p className="mt-2 text-muted-foreground">
            Take a 30-second skill assessment to generate a personalized AI engineer roadmap.
          </p>
          <Link
            href="/onboarding"
            className="mt-4 inline-block rounded-md bg-primary px-5 py-2.5 text-primary-foreground hover:opacity-90"
          >
            Start assessment
          </Link>
        </div>
      )}

      {recent.length > 0 ? (
        <section className="rounded-lg border border-border p-6">
          <h2 className="text-xl font-semibold">Recent activity</h2>
          <ul className="mt-3 divide-y divide-border">
            {recent.map((entry) => (
              <li key={entry.slug} className="flex items-center justify-between py-3">
                <div>
                  <Link href={`/learn/${entry.slug}`} className="font-medium hover:underline">
                    {entry.title}
                  </Link>
                  <div className="text-xs text-muted-foreground">
                    Phase {entry.phase} · {entry.phase_title}
                  </div>
                </div>
                <div className="flex items-center gap-3 text-sm">
                  <span className="text-muted-foreground">
                    Best score: {Math.round(entry.mastery_score * 100)}%
                  </span>
                  <span
                    className={
                      "rounded-full px-2 py-0.5 text-xs font-medium " +
                      (entry.completed
                        ? "bg-emerald-100 text-emerald-900"
                        : "bg-slate-100 text-slate-700")
                    }
                  >
                    {entry.completed ? "Completed" : "In progress"}
                  </span>
                </div>
              </li>
            ))}
          </ul>
        </section>
      ) : null}
    </div>
  );
}
