import Link from "next/link";
import { notFound } from "next/navigation";

import { getLesson, listMyInterviews, type InterviewListEntry } from "@/lib/api";
import { InterviewRunner } from "@/components/interview-runner";

export const dynamic = "force-dynamic";

function pickResumeCandidate(
  interviews: InterviewListEntry[],
  slug: string
): InterviewListEntry | null {
  // Most recent unfinished interview for this slug, if any.
  return (
    interviews.find((i) => i.slug === slug && !i.finished) ?? null
  );
}

export default async function InterviewPage({ params }: { params: { slug: string } }) {
  const lesson = await getLesson(params.slug);
  if (!lesson) notFound();

  let interviews: InterviewListEntry[] = [];
  try {
    interviews = await listMyInterviews();
  } catch {
    // The interview history is a nice-to-have; don't crash the page.
    interviews = [];
  }
  const resumable = pickResumeCandidate(interviews, params.slug);
  const priorAttempts = interviews.filter((i) => i.slug === params.slug && i.finished);

  return (
    <div className="space-y-8">
      <header className="space-y-2">
        <div className="text-xs uppercase tracking-wide text-muted-foreground">
          Phase {lesson.phase} · {lesson.phase_title} · Mock interview
        </div>
        <h1 className="text-3xl font-semibold">{lesson.title}</h1>
        <p className="text-sm text-muted-foreground">
          A short viva-style interview. Four questions, scored 0–100. Your transcript and grade
          are saved so you can review later.
        </p>
        <div className="flex flex-wrap gap-3 pt-1 text-sm text-muted-foreground">
          <Link
            href={`/learn/${lesson.slug}`}
            className="underline-offset-4 hover:underline"
          >
            ← Re-read the lesson
          </Link>
          <Link
            href={`/quiz/${lesson.slug}`}
            className="underline-offset-4 hover:underline"
          >
            Take the quiz →
          </Link>
        </div>
      </header>

      <InterviewRunner slug={params.slug} initialInterview={null} />

      {resumable ? (
        <p className="text-xs text-muted-foreground">
          Unfinished interview from {new Date(resumable.created_at).toLocaleString()}. Starting a
          new one will keep the old transcript on your history page.
        </p>
      ) : null}

      {priorAttempts.length ? (
        <section className="space-y-2 rounded-lg border border-border bg-card p-4">
          <h2 className="text-sm font-medium">Your prior attempts on this topic</h2>
          <ul className="space-y-1 text-sm text-muted-foreground">
            {priorAttempts.slice(0, 5).map((a) => (
              <li key={a.id} className="flex items-center justify-between">
                <span>{new Date(a.created_at).toLocaleString()}</span>
                <span
                  className={
                    "rounded-full border px-2 py-0.5 text-xs " +
                    (a.score !== null && a.score >= 70
                      ? "border-emerald-300 bg-emerald-50 text-emerald-900"
                      : "border-amber-300 bg-amber-50 text-amber-900")
                  }
                >
                  Score {a.score !== null ? Math.round(a.score) : "—"} / 100
                </span>
              </li>
            ))}
          </ul>
        </section>
      ) : null}
    </div>
  );
}
