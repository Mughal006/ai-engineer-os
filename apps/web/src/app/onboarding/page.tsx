import { AssessmentForm } from "@/components/assessment-form";

export default function OnboardingPage() {
  return (
    <div className="mx-auto max-w-2xl space-y-6">
      <div>
        <h1 className="text-3xl font-semibold">Skill assessment</h1>
        <p className="text-muted-foreground">
          Answer a few questions and we&apos;ll generate a personalized AI engineer roadmap.
        </p>
      </div>
      <AssessmentForm />
    </div>
  );
}
