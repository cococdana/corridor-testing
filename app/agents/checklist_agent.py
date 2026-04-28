from __future__ import annotations

from app.agents.base import AgentResult
from app.schemas import JobAnalysis, MatchAnalysis


class ChecklistAgent:
    name = "checklist"

    def run(self, job: JobAnalysis, match: MatchAnalysis) -> AgentResult[list[str]]:
        items: list[str] = [
            "Rename resume file to: FirstLast - " + (job.role or "Role") + " - Resume.pdf",
            "Tailor the top summary to mention 2–3 must-have skills from the posting.",
            "Ensure experience bullets include metrics (scale, latency, $ impact, time saved).",
            "Add links: GitHub/portfolio/LinkedIn (if applicable).",
            "Double-check location/visa/availability fields match the application.",
        ]
        if match.missing_must_haves:
            items.append("Add explicit proof (resume bullet or short note) for: " + ", ".join(match.missing_must_haves[:4]) + ".")
        items += [
            "Draft a short follow-up message (send 3–5 business days after applying).",
            "Log the application: company, role, date, source, referral, next step.",
        ]
        return AgentResult(agent=self.name, output=items, meta={"item_count": len(items)})

