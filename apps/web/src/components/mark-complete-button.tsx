"use client";

import { useState, useTransition } from "react";
import { useRouter } from "next/navigation";

function absoluteUrl(path: string): string {
  // Build an absolute URL from `location.origin` instead of letting fetch
  // resolve against `document.baseURI`, which can carry HTTP basic-auth
  // credentials when the page is served behind a credentialed tunnel —
  // those would otherwise throw "URL includes credentials" in Chrome.
  if (typeof window === "undefined") return path;
  return new URL(path, window.location.origin).toString();
}

export function MarkCompleteButton({ slug }: { slug: string }) {
  const router = useRouter();
  const [pending, startTransition] = useTransition();
  const [done, setDone] = useState(false);
  const [error, setError] = useState<string | null>(null);

  return (
    <div className="flex items-center gap-3">
      <button
        type="button"
        disabled={pending || done}
        onClick={() => {
          setError(null);
          startTransition(async () => {
            try {
              const res = await fetch(absoluteUrl(`/api/lessons/${slug}/complete`), {
                method: "POST"
              });
              const body = await res.json().catch(() => ({}));
              if (!res.ok || body?.ok === false) {
                throw new Error(body?.error ?? `HTTP ${res.status}`);
              }
              setDone(true);
              router.refresh();
            } catch (err) {
              setError(err instanceof Error ? err.message : "Failed to mark complete.");
            }
          });
        }}
        className="rounded-md bg-primary px-4 py-2 text-sm text-primary-foreground hover:opacity-90 disabled:opacity-60"
      >
        {done ? "Marked complete" : pending ? "Saving…" : "Mark lesson as read"}
      </button>
      {error ? <span className="text-sm text-red-600">{error}</span> : null}
    </div>
  );
}
