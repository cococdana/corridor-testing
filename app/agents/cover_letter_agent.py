from __future__ import annotations

from app.agents.base import AgentResult
from app.schemas import JobAnalysis, MatchAnalysis, Preferences, ResumeSummary


class CoverLetterAgent:
    name = "cover_letter"

    def run(
        self,
        job: JobAnalysis,
        resume: ResumeSummary,
        match: MatchAnalysis,
        preferences: Preferences | None,
    ) -> AgentResult[str]:
        prefs = preferences or Preferences()
        tone = prefs.tone

        role = job.role if job.role != "Unknown" else "the role"
        company = job.company if job.company != "Unknown" else "your team"

        opener = {
            "direct": f"I'm applying for {role}. I’ve built and shipped systems aligned with what {company} is asking for.",
            "warm": f"Thanks for considering my application for {role}. I’m excited about the chance to contribute at {company}.",
            "confident": f"I’m applying for {role} and believe my background maps strongly to what {company} needs.",
            "humble": f"I’d like to apply for {role}. I think my experience could be useful to {company}.",
        }[tone]

        matched = match.matched_must_haves[:4]
        missing = match.missing_must_haves[:2]
        focus = [f for f in (prefs.focus or []) if isinstance(f, str)][:3]

        para2_parts: list[str] = []
        if matched:
            para2_parts.append("Relevant strengths include " + ", ".join(matched) + ".")
        if focus:
            para2_parts.append("I’d emphasize " + ", ".join(focus) + ".")
        if resume.key_bullets:
            para2_parts.append("Recent work highlights: " + "; ".join(resume.key_bullets[:2]) + ".")
        para2 = " ".join(para2_parts).strip() or "I’d bring a practical, delivery-focused approach and collaborate closely across functions."

        para3 = ""
        if missing:
            para3 = (
                "A quick note on gaps: "
                + ", ".join(missing)
                + " aren’t prominent on my resume today, but I can ramp quickly and have adjacent experience I can demonstrate."
            )

        close = "If helpful, I can share a short work sample or walk through a recent project that matches this role’s core requirements. Thanks for your time."

        paragraphs = [opener, para2]
        if para3:
            paragraphs.append(para3)
        paragraphs.append(close)

        # Bound paragraph count.
        paragraphs = paragraphs[: max(2, prefs.max_cover_letter_paragraphs)]

        letter = "\n\n".join(paragraphs)
        return AgentResult(agent=self.name, output=letter, meta={"tone": tone, "paragraphs": len(paragraphs)})

