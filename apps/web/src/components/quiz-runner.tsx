"use client";

import { useState, useTransition } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";

import type { Quiz, QuizResult } from "@/lib/api";

function absoluteUrl(path: string): string {
  if (typeof window === "undefined") return path;
  return new URL(path, window.location.origin).toString();
}

export function QuizRunner({ quiz }: { quiz: Quiz }) {
  const router = useRouter();
  const [answers, setAnswers] = useState<Record<number, number>>({});
  const [result, setResult] = useState<QuizResult | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [pending, startTransition] = useTransition();

  const allAnswered = quiz.questions.every((q) => answers[q.index] !== undefined);

  function pick(qIndex: number, optionIndex: number) {
    setAnswers((prev) => ({ ...prev, [qIndex]: optionIndex }));
  }

  function submit() {
    setError(null);
    startTransition(async () => {
      try {
        const payload = quiz.questions.map((q) => answers[q.index]);
        const res = await fetch(absoluteUrl(`/api/quizzes/${quiz.slug}/submit`), {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ answers: payload })
        });
        const body = await res.json().catch(() => ({}));
        if (!res.ok || body?.ok === false) {
          throw new Error(body?.error ?? `HTTP ${res.status}`);
        }
        setResult(body.result as QuizResult);
        router.refresh();
      } catch (err) {
        setError(err instanceof Error ? err.message : "Failed to submit quiz.");
      }
    });
  }

  function reset() {
    setAnswers({});
    setResult(null);
    setError(null);
  }

  if (result) {
    return (
      <div className="space-y-6">
        <div
          className={
            "rounded-lg border p-6 " +
            (result.passed ? "border-emerald-300 bg-emerald-50" : "border-amber-300 bg-amber-50")
          }
        >
          <h2 className="text-2xl font-semibold">
            {result.passed ? "Passed" : "Not yet"} — {Math.round(result.score * 100)}%
          </h2>
          <p className="mt-1 text-sm text-muted-foreground">
            Passing score: {Math.round(result.passing_score * 100)}%. Best score over{" "}
            {result.attempts} attempt(s): {Math.round(result.mastery_score * 100)}%.
          </p>
        </div>

        <ol className="space-y-4">
          {quiz.questions.map((q) => {
            const r = result.per_question[q.index];
            const picked = answers[q.index];
            return (
              <li key={q.index} className="rounded-lg border border-border p-4">
                <div className="flex items-baseline justify-between">
                  <p className="font-medium">
                    Q{q.index + 1}. {q.prompt}
                  </p>
                  <span
                    className={
                      "text-xs font-medium " + (r.correct ? "text-emerald-700" : "text-rose-700")
                    }
                  >
                    {r.correct ? "Correct" : "Wrong"}
                  </span>
                </div>
                <ul className="mt-2 space-y-1 text-sm">
                  {q.options.map((opt, i) => {
                    const isPicked = picked === i;
                    const isCorrect = r.correct_index === i;
                    return (
                      <li
                        key={i}
                        className={
                          "rounded px-2 py-1 " +
                          (isCorrect
                            ? "bg-emerald-100 text-emerald-900"
                            : isPicked
                              ? "bg-rose-100 text-rose-900"
                              : "")
                        }
                      >
                        {opt}
                        {isCorrect ? " ✓" : isPicked && !isCorrect ? " ✗" : ""}
                      </li>
                    );
                  })}
                </ul>
                <p className="mt-2 text-xs text-muted-foreground">{r.explanation}</p>
              </li>
            );
          })}
        </ol>

        <div className="flex gap-3">
          <button
            type="button"
            onClick={reset}
            className="rounded-md bg-primary px-4 py-2 text-sm text-primary-foreground hover:opacity-90"
          >
            Try again
          </button>
          <Link
            href={`/learn/${quiz.slug}`}
            className="rounded-md border border-border px-4 py-2 text-sm hover:bg-accent"
          >
            Back to lesson
          </Link>
          <Link
            href="/dashboard"
            className="ml-auto text-sm text-muted-foreground underline-offset-4 hover:underline"
          >
            View dashboard
          </Link>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <ol className="space-y-4">
        {quiz.questions.map((q) => (
          <li key={q.index} className="rounded-lg border border-border p-4">
            <p className="font-medium">
              Q{q.index + 1}. {q.prompt}
            </p>
            <ul className="mt-3 space-y-2">
              {q.options.map((opt, i) => (
                <li key={i}>
                  <label className="flex cursor-pointer items-start gap-2 rounded px-2 py-1 hover:bg-accent">
                    <input
                      type="radio"
                      name={`q-${q.index}`}
                      value={i}
                      checked={answers[q.index] === i}
                      onChange={() => pick(q.index, i)}
                      className="mt-1"
                    />
                    <span className="text-sm">{opt}</span>
                  </label>
                </li>
              ))}
            </ul>
          </li>
        ))}
      </ol>

      <div className="flex items-center gap-3">
        <button
          type="button"
          onClick={submit}
          disabled={!allAnswered || pending}
          className="rounded-md bg-primary px-5 py-2.5 text-primary-foreground hover:opacity-90 disabled:opacity-60"
        >
          {pending ? "Grading…" : "Submit answers"}
        </button>
        {!allAnswered ? (
          <span className="text-sm text-muted-foreground">
            Answer all {quiz.questions.length} questions to submit.
          </span>
        ) : null}
        {error ? <span className="text-sm text-red-600">{error}</span> : null}
      </div>
    </div>
  );
}
