from __future__ import annotations

import re

from app.agents.base import AgentResult
from app.agents.skill_extract import DEFAULT_SKILLS, extract_bullets, extract_skills, normalize_text
from app.schemas import ResumeSummary


class ResumeSummaryAgent:
    name = "resume_summary"

    def run(self, resume_text: str) -> AgentResult[ResumeSummary]:
        text = normalize_text(resume_text)
        skills = extract_skills(text, DEFAULT_SKILLS)

        bullets = extract_bullets(resume_text, max_items=10)
        if not bullets:
            bullets = self._fallback_sentences(resume_text, max_items=6)

        headline = self._infer_headline(resume_text, skills)

        return AgentResult(
            agent=self.name,
            output=ResumeSummary(headline=headline, extracted_skills=skills, key_bullets=bullets),
            meta={"skill_count": len(skills), "bullet_count": len(bullets)},
        )

    def _infer_headline(self, resume_text: str, skills: list[str]) -> str:
        # Heuristic: first non-empty line, otherwise synthesize.
        for ln in resume_text.splitlines():
            s = ln.strip()
            if s and len(s) <= 120:
                return s
        top = ", ".join(skills[:4])
        if top:
            return f"Experienced professional ({top})"
        return "Experienced professional"

    def _fallback_sentences(self, resume_text: str, max_items: int) -> list[str]:
        blob = re.sub(r"\s+", " ", resume_text.strip())
        parts = [p.strip() for p in re.split(r"[.!?]\s+", blob) if p.strip()]
        return parts[:max_items]

