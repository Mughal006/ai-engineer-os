import { NextResponse, type NextRequest } from "next/server";
import { submitQuiz } from "@/lib/api";

export async function POST(req: NextRequest, { params }: { params: { slug: string } }) {
  let payload: { answers?: unknown };
  try {
    payload = (await req.json()) as { answers?: unknown };
  } catch {
    return NextResponse.json({ ok: false, error: "Invalid JSON body." }, { status: 400 });
  }
  const answers = payload.answers;
  if (!Array.isArray(answers) || !answers.every((a) => Number.isInteger(a))) {
    return NextResponse.json(
      { ok: false, error: "Body must be { answers: integer[] }." },
      { status: 400 }
    );
  }
  try {
    const result = await submitQuiz(params.slug, answers as number[]);
    return NextResponse.json({ ok: true, result });
  } catch (err) {
    const message = err instanceof Error ? err.message : "Failed to submit quiz.";
    return NextResponse.json({ ok: false, error: message }, { status: 500 });
  }
}
