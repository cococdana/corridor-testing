from __future__ import annotations

from app.agents.base import AgentResult
from app.schemas import JobAnalysis, MatchAnalysis, ResumeSummary


class MatcherAgent:
    name = "matcher"

    def run(self, job: JobAnalysis, resume: ResumeSummary) -> AgentResult[MatchAnalysis]:
        resume_skills = set(resume.extracted_skills)
        must = list(job.must_have_skills)
        nice = list(job.nice_to_have_skills)

        matched_must = sorted([s for s in must if s in resume_skills])
        missing_must = sorted([s for s in must if s not in resume_skills])
        matched_nice = sorted([s for s in nice if s in resume_skills])

        # Score: weighted overlap. Keep simple + transparent.
        denom = max(1, len(must) + 0.5 * len(nice))
        numer = len(matched_must) + 0.5 * len(matched_nice)
        score = float(min(1.0, numer / denom))

        suggested_edits: list[str] = []
        if missing_must:
            suggested_edits.append(
                "Add a 'Skills' subsection (or expand it) to explicitly mention: " + ", ".join(missing_must[:6]) + "."
            )
        if matched_must:
            suggested_edits.append(
                "Add/adjust 1–2 bullets to quantify impact using: " + ", ".join(matched_must[:4]) + "."
            )
        if not resume.key_bullets:
            suggested_edits.append("Convert experience into concise bullets with metrics (latency, revenue, scale, cost).")

        out = MatchAnalysis(
            score=score,
            matched_must_haves=matched_must,
            missing_must_haves=missing_must,
            matched_nice_to_haves=matched_nice,
            suggested_resume_edits=suggested_edits,
        )
        return AgentResult(agent=self.name, output=out, meta={"must_count": len(must), "nice_count": len(nice)})

