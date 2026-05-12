import Link from "next/link";
import { notFound } from "next/navigation";

import { getQuiz } from "@/lib/api";
import { QuizRunner } from "@/components/quiz-runner";

export const dynamic = "force-dynamic";

export default async function QuizPage({ params }: { params: { slug: string } }) {
  const quiz = await getQuiz(params.slug);
  if (!quiz) notFound();

  return (
    <div className="space-y-6">
      <header className="space-y-2">
        <div className="text-xs uppercase tracking-wide text-muted-foreground">
          Phase {quiz.phase} · {quiz.phase_title} · Quiz
        </div>
        <h1 className="text-3xl font-semibold">{quiz.title}</h1>
        <p className="text-sm text-muted-foreground">
          {quiz.questions.length} questions · pass with {Math.round(quiz.passing_score * 100)}%
          or higher.
        </p>
        <Link
          href={`/learn/${quiz.slug}`}
          className="inline-block text-sm text-muted-foreground underline-offset-4 hover:underline"
        >
          ← Re-read the lesson
        </Link>
      </header>

      <QuizRunner quiz={quiz} />
    </div>
  );
}
