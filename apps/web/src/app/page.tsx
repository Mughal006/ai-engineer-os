import Link from "next/link";
import { SignedIn, SignedOut, SignInButton } from "@clerk/nextjs";

const FEATURES = [
  { title: "Adaptive roadmap", body: "A personalized 12-week plan that adjusts as you grow." },
  { title: "Mastery-based progression", body: "Topics unlock only when you've earned them." },
  { title: "AI tutor & interviewer", body: "On-demand explanations and realistic mock interviews." },
  { title: "Coding sandbox", body: "Run code, get auto-graded feedback, build a portfolio." },
  { title: "Productivity analytics", body: "Track focus, distraction, and learning efficiency." },
  { title: "Anti-cheat assessments", body: "Browser monitoring keeps progress real." }
];

export default function HomePage() {
  return (
    <div className="space-y-16">
      <section className="space-y-6 py-10 text-center">
        <h1 className="text-balance text-5xl font-bold tracking-tight">
          Become a job-ready AI engineer.
        </h1>
        <p className="mx-auto max-w-2xl text-balance text-lg text-muted-foreground">
          AI Engineer OS is an adaptive learning platform: roadmap planner, AI tutor, mock
          interviewer, and coding coach in one product.
        </p>
        <div className="flex justify-center gap-3">
          <SignedOut>
            <SignInButton mode="modal">
              <button className="rounded-md bg-primary px-5 py-2.5 text-primary-foreground hover:opacity-90">
                Get started
              </button>
            </SignInButton>
          </SignedOut>
          <SignedIn>
            <Link
              href="/dashboard"
              className="rounded-md bg-primary px-5 py-2.5 text-primary-foreground hover:opacity-90"
            >
              Go to dashboard
            </Link>
          </SignedIn>
          <Link
            href="/roadmap"
            className="rounded-md border border-border px-5 py-2.5 hover:bg-accent"
          >
            Preview a roadmap
          </Link>
        </div>
      </section>

      <section className="grid grid-cols-1 gap-4 md:grid-cols-3">
        {FEATURES.map((f) => (
          <div key={f.title} className="rounded-lg border border-border p-5">
            <h3 className="font-semibold">{f.title}</h3>
            <p className="mt-1 text-sm text-muted-foreground">{f.body}</p>
          </div>
        ))}
      </section>
    </div>
  );
}
