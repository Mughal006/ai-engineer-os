import type { Metadata } from "next";
import { ClerkProvider, SignedIn, SignedOut, SignInButton, UserButton } from "@clerk/nextjs";
import Link from "next/link";
import { Fragment } from "react";
import "./globals.css";

const DEMO_MODE = process.env.NEXT_PUBLIC_DEMO_MODE === "true";

export const metadata: Metadata = {
  title: "AI Engineer OS",
  description: "An adaptive learning platform that turns beginners into AI engineers."
};

function ClerkHeader() {
  return (
    <nav className="flex items-center gap-4 text-sm">
      <SignedIn>
        <Link href="/dashboard" className="text-muted-foreground hover:text-foreground">
          Dashboard
        </Link>
        <Link href="/roadmap" className="text-muted-foreground hover:text-foreground">
          Roadmap
        </Link>
        <UserButton afterSignOutUrl="/" />
      </SignedIn>
      <SignedOut>
        <SignInButton mode="modal">
          <button className="rounded-md bg-primary px-3 py-1.5 text-sm text-primary-foreground hover:opacity-90">
            Sign in
          </button>
        </SignInButton>
      </SignedOut>
    </nav>
  );
}

function DemoHeader() {
  return (
    <nav className="flex items-center gap-4 text-sm">
      <Link href="/dashboard" className="text-muted-foreground hover:text-foreground">
        Dashboard
      </Link>
      <Link href="/roadmap" className="text-muted-foreground hover:text-foreground">
        Roadmap
      </Link>
      <span className="rounded-full border border-amber-300 bg-amber-50 px-2.5 py-0.5 text-xs font-medium text-amber-900">
        Demo mode
      </span>
    </nav>
  );
}

export default function RootLayout({ children }: { children: React.ReactNode }) {
  const Wrapper = DEMO_MODE ? Fragment : ClerkProvider;
  return (
    <Wrapper>
      <html lang="en">
        <body>
          <header className="border-b border-border">
            <div className="mx-auto flex max-w-6xl items-center justify-between px-6 py-4">
              <Link href="/" className="text-lg font-semibold">
                AI Engineer OS
              </Link>
              {DEMO_MODE ? <DemoHeader /> : <ClerkHeader />}
            </div>
          </header>
          <main className="mx-auto max-w-6xl px-6 py-8">{children}</main>
        </body>
      </html>
    </Wrapper>
  );
}
