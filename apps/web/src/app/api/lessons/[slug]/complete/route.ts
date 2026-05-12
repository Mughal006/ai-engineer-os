import { NextResponse } from "next/server";
import { markLessonComplete } from "@/lib/api";

export async function POST(_req: Request, { params }: { params: { slug: string } }) {
  try {
    const result = await markLessonComplete(params.slug);
    return NextResponse.json({ ok: true, ...result });
  } catch (err) {
    const message = err instanceof Error ? err.message : "Failed to mark complete.";
    return NextResponse.json({ ok: false, error: message }, { status: 500 });
  }
}
