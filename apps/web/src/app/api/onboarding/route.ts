import { NextResponse, type NextRequest } from "next/server";
import { createRoadmap, type SkillAssessment } from "@/lib/api";

export async function POST(req: NextRequest) {
  let payload: SkillAssessment;
  try {
    payload = (await req.json()) as SkillAssessment;
  } catch {
    return NextResponse.json({ ok: false, error: "Invalid JSON body." }, { status: 400 });
  }
  try {
    await createRoadmap(payload);
    return NextResponse.json({ ok: true });
  } catch (err) {
    const message = err instanceof Error ? err.message : "Failed to generate roadmap.";
    return NextResponse.json({ ok: false, error: message }, { status: 500 });
  }
}
