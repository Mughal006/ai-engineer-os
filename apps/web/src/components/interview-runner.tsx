"use client";

import { useEffect, useRef, useState, useTransition } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";

import type { Interview, InterviewTurn } from "@/lib/api";

function absoluteUrl(path: string): string {
  if (typeof window === "undefined") return path;
  return new URL(path, window.location.origin).toString();
}

function passingBadgeClass(score: number, passing: number): string {
  return score >= passing
    ? "border-emerald-300 bg-emerald-50 text-emerald-900"
    : "border-amber-300 bg-amber-50 text-amber-900";
}

function turnRoleLabel(turn: InterviewTurn): string {
  switch (turn.kind) {
    case "question":
      return `Interviewer · Q${turn.index}`;
    case "answer":
      return `You · A${turn.index}`;
    case "feedback":
      return `Grader · Q${turn.index}`;
    case "final":
      return "Final feedback";
  }
}

export function InterviewRunner({
  slug,
  initialInterview
}: {
  slug: string;
  initialInterview: Interview | null;
}) {
  const router = useRouter();
  const [interview, setInterview] = useState<Interview | null>(initialInterview);
  const [draft, setDraft] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [pending, startTransition] = useTransition();
  const scrollerRef = useRef<HTMLDivElement | null>(null);

  // Auto-scroll the transcript when new turns arrive.
  useEffect(() => {
    const node = scrollerRef.current;
    if (node) node.scrollTop = node.scrollHeight;
  }, [interview?.transcript.length]);

  function start() {
    setError(null);
    startTransition(async () => {
      try {
        const res = await fetch(absoluteUrl(`/api/interviews/start`), {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ slug })
        });
        const body = await res.json().catch(() => ({}));
        if (!res.ok || body?.ok === false) {
          throw new Error(body?.error ?? `HTTP ${res.status}`);
        }
        setInterview(body.interview as Interview);
        router.refresh();
      } catch (err) {
        setError(err instanceof Error ? err.message : "Failed to start interview.");
      }
    });
  }

  function submit() {
    if (!interview) return;
    const answer = draft.trim();
    if (!answer) return;
    setError(null);
    startTransition(async () => {
      try {
        const res = await fetch(
          absoluteUrl(`/api/interviews/${encodeURIComponent(interview.id)}/answer`),
          {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ answer })
          }
        );
        const body = await res.json().catch(() => ({}));
        if (!res.ok || body?.ok === false) {
          throw new Error(body?.error ?? `HTTP ${res.status}`);
        }
        setInterview(body.interview as Interview);
        setDraft("");
        router.refresh();
      } catch (err) {
        setError(err instanceof Error ? err.message : "Failed to post answer.");
      }
    });
  }

  if (!interview) {
    return (
      <div className="space-y-4 rounded-lg border border-border bg-card p-6">
        <h2 className="text-xl font-semibold">Ready when you are.</h2>
        <p className="text-sm text-muted-foreground">
          The interviewer will ask {4} short questions about this topic, score each answer, and
          give you a final write-up. No webcam, no timer — just like a viva.
        </p>
        {error ? <p className="text-sm text-rose-700">{error}</p> : null}
        <button
          type="button"
          onClick={start}
          disabled={pending}
          className="rounded-md bg-primary px-4 py-2 text-sm text-primary-foreground hover:opacity-90 disabled:opacity-50"
        >
          {pending ? "Starting…" : "Start mock interview"}
        </button>
      </div>
    );
  }

  const transcript = interview.transcript;
  const openQuestion = !interview.finished
    ? [...transcript].reverse().find((t) => t.kind === "question") ?? null
    : null;
  const awaitingAnswer = Boolean(openQuestion) && !lastUserAnswerMatches(transcript, openQuestion);

  return (
    <div className="space-y-6">
      <div className="flex flex-wrap items-baseline justify-between gap-2">
        <p className="text-sm text-muted-foreground">
          Question {interview.question_index} of {interview.total_questions} ·{" "}
          {interview.finished ? "Interview complete" : "In progress"}
        </p>
        {interview.finished && interview.score !== null ? (
          <span
            className={
              "rounded-full border px-3 py-1 text-xs font-medium " +
              passingBadgeClass(interview.score, interview.passing_score)
            }
          >
            Score {Math.round(interview.score)} / 100 · passes at {interview.passing_score}
          </span>
        ) : null}
      </div>

      <div
        ref={scrollerRef}
        className="max-h-[560px] space-y-4 overflow-y-auto rounded-lg border border-border bg-card p-4"
      >
        {transcript.map((turn, i) => (
          <article key={i} className="space-y-1">
            <p className="text-[11px] uppercase tracking-wide text-muted-foreground">
              {turnRoleLabel(turn)}
              {typeof turn.score === "number" && turn.kind === "feedback"
                ? ` · ${Math.round(turn.score)}/100`
                : ""}
            </p>
            <p
              className={
                "whitespace-pre-wrap rounded-md px-3 py-2 text-sm " +
                turnBubbleClass(turn)
              }
            >
              {turn.content}
            </p>
          </article>
        ))}
      </div>

      {interview.finished ? (
        <div className="flex flex-wrap items-center gap-3">
          <Link
            href={`/learn/${interview.slug}`}
            className="rounded-md border border-border px-4 py-2 text-sm hover:bg-accent"
          >
            Back to lesson
          </Link>
          <Link
            href={`/quiz/${interview.slug}`}
            className="rounded-md border border-border px-4 py-2 text-sm hover:bg-accent"
          >
            Take the quiz →
          </Link>
          <button
            type="button"
            onClick={() => {
              setInterview(null);
              setDraft("");
              setError(null);
            }}
            className="ml-auto rounded-md bg-primary px-4 py-2 text-sm text-primary-foreground hover:opacity-90"
          >
            Start another interview
          </button>
        </div>
      ) : awaitingAnswer ? (
        <form
          onSubmit={(e) => {
            e.preventDefault();
            submit();
          }}
          className="space-y-3"
        >
          <textarea
            value={draft}
            onChange={(e) => setDraft(e.target.value)}
            disabled={pending}
            rows={5}
            placeholder="Type your answer like you would explain it out loud…"
            className="w-full rounded-md border border-border bg-background px-3 py-2 text-sm focus:border-primary focus:outline-none"
          />
          {error ? <p className="text-sm text-rose-700">{error}</p> : null}
          <div className="flex items-center gap-3">
            <button
              type="submit"
              disabled={pending || !draft.trim()}
              className="rounded-md bg-primary px-4 py-2 text-sm text-primary-foreground hover:opacity-90 disabled:opacity-50"
            >
              {pending ? "Sending…" : "Submit answer"}
            </button>
            <p className="text-xs text-muted-foreground">
              Tip: name the concept, give an example, and mention a production trade-off.
            </p>
          </div>
        </form>
      ) : (
        <p className="text-sm text-muted-foreground">Loading the next question…</p>
      )}
    </div>
  );
}

function turnBubbleClass(turn: InterviewTurn): string {
  switch (turn.kind) {
    case "question":
      return "bg-muted text-foreground";
    case "answer":
      return "bg-primary/10 text-foreground";
    case "feedback":
      return "border border-border bg-background text-foreground";
    case "final":
      return "border border-emerald-300 bg-emerald-50 text-emerald-900";
  }
}

function lastUserAnswerMatches(transcript: InterviewTurn[], question: InterviewTurn | null) {
  if (!question) return false;
  // True if the user has already answered the latest question (so we hide the form).
  for (let i = transcript.length - 1; i >= 0; i--) {
    const t = transcript[i];
    if (t === question) return false;
    if (t.kind === "answer" && t.index === question.index) return true;
  }
  return false;
}
