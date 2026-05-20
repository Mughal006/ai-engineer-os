import { NextResponse, type NextRequest } from "next/server";
import { startInterview } from "@/lib/api";

export async function POST(req: NextRequest) {
  let payload: { slug?: unknown };
  try {
    payload = (await req.json()) as { slug?: unknown };
  } catch {
    return NextResponse.json({ ok: false, error: "Invalid JSON body." }, { status: 400 });
  }
  if (typeof payload.slug !== "string" || !payload.slug) {
    return NextResponse.json(
      { ok: false, error: "Body must be { slug: string }." },
      { status: 400 }
    );
  }
  try {
    const interview = await startInterview(payload.slug);
    return NextResponse.json({ ok: true, interview });
  } catch (err) {
    const message = err instanceof Error ? err.message : "Failed to start interview.";
    const status = message.startsWith("API 404") ? 404 : 500;
    return NextResponse.json({ ok: false, error: message }, { status });
  }
}
