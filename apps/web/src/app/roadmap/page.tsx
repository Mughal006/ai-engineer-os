import Link from "next/link";
import { getMyRoadmap } from "@/lib/api";
import { RoadmapView } from "@/components/roadmap-view";

export const dynamic = "force-dynamic";

export default async function RoadmapPage() {
  const roadmap = await getMyRoadmap().catch(() => null);

  if (!roadmap) {
    return (
      <div className="rounded-lg border border-dashed border-border p-10 text-center">
        <h2 className="text-xl font-medium">No active roadmap</h2>
        <p className="mt-2 text-muted-foreground">
          Generate one from your skill assessment to see weekly phases and daily tasks here.
        </p>
        <Link
          href="/onboarding"
          className="mt-4 inline-block rounded-md bg-primary px-5 py-2.5 text-primary-foreground hover:opacity-90"
        >
          Start assessment
        </Link>
      </div>
    );
  }

  return <RoadmapView roadmap={roadmap} />;
}
