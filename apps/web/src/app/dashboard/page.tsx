import Link from "next/link";
import { getMyRoadmap } from "@/lib/api";
import { RoadmapSummary } from "@/components/roadmap-summary";

export const dynamic = "force-dynamic";

export default async function DashboardPage() {
  const roadmap = await getMyRoadmap().catch(() => null);

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
        <RoadmapSummary roadmap={roadmap} />
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
    </div>
  );
}
