import Link from "next/link";
import { notFound } from "next/navigation";

import { getLesson } from "@/lib/api";
import { LessonView } from "@/components/lesson-view";
import { MarkCompleteButton } from "@/components/mark-complete-button";

export const dynamic = "force-dynamic";

export default async function LessonPage({ params }: { params: { slug: string } }) {
  const lesson = await getLesson(params.slug);
  if (!lesson) notFound();

  return (
    <div className="space-y-8">
      <header className="space-y-2">
        <div className="text-xs uppercase tracking-wide text-muted-foreground">
          Phase {lesson.phase} · {lesson.phase_title}
        </div>
        <h1 className="text-3xl font-semibold">{lesson.title}</h1>
        <p className="text-sm text-muted-foreground">
          Estimated read time: {lesson.estimated_minutes} minutes.
        </p>
      </header>

      <LessonView lesson={lesson} />

      <div className="flex flex-wrap items-center gap-3">
        <MarkCompleteButton slug={lesson.slug} />
        <Link
          href={`/quiz/${lesson.slug}`}
          className="rounded-md border border-border px-4 py-2 text-sm hover:bg-accent"
        >
          Take the quiz →
        </Link>
        <Link
          href="/roadmap"
          className="ml-auto text-sm text-muted-foreground underline-offset-4 hover:underline"
        >
          Back to roadmap
        </Link>
      </div>
    </div>
  );
}
