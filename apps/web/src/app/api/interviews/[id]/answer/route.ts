import { NextResponse, type NextRequest } from "next/server";
import { postInterviewAnswer } from "@/lib/api";

export async function POST(req: NextRequest, { params }: { params: { id: string } }) {
  let payload: { answer?: unknown };
  try {
    payload = (await req.json()) as { answer?: unknown };
  } catch {
    return NextResponse.json({ ok: false, error: "Invalid JSON body." }, { status: 400 });
  }
  if (typeof payload.answer !== "string" || !payload.answer.trim()) {
    return NextResponse.json(
      { ok: false, error: "Body must be { answer: string }." },
      { status: 400 }
    );
  }
  try {
    const interview = await postInterviewAnswer(params.id, payload.answer);
    return NextResponse.json({ ok: true, interview });
  } catch (err) {
    const message = err instanceof Error ? err.message : "Failed to post answer.";
    const status =
      message.startsWith("API 404")
        ? 404
        : message.startsWith("API 409")
          ? 409
          : 500;
    return NextResponse.json({ ok: false, error: message }, { status });
  }
}
