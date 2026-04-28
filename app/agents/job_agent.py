from __future__ import annotations

import re

from app.agents.base import AgentResult
from app.agents.skill_extract import DEFAULT_SKILLS, extract_skills, normalize_text
from app.schemas import JobAnalysis


class JobAnalysisAgent:
    name = "job_analysis"

    def run(self, job_description: str) -> AgentResult[JobAnalysis]:
        text = normalize_text(job_description)

        company = self._extract_company(job_description)
        role = self._extract_role(text)

        must_have = self._extract_section_skills(
            text,
            section_patterns=[
                r"(?:required|must have|must-have|requirements|qualifications|skills needed|what we're looking for|what we are looking for)[:\s]*(.*?)(?:\n\n|preferred|nice to have|about you|$)",
            ],
        )
        nice_to_have = self._extract_section_skills(
            text,
            section_patterns=[
                r"(?:preferred|nice to have|nice-to-have|bonus|plus)[:\s]*(.*?)(?:\n\n|about you|$)",
            ],
        )

        keywords = extract_skills(text, DEFAULT_SKILLS)
        if not keywords:
            keywords = self._fallback_keywords(text)

        if not must_have:
            must_have = keywords[:5]

        analysis = JobAnalysis(
            company=company,
            role=role,
            must_have_skills=must_have[:8],
            nice_to_have_skills=nice_to_have[:8],
            keywords=keywords,
        )
        return AgentResult(agent=self.name, output=analysis, meta={"keyword_count": len(keywords)})

    def _extract_company(self, raw_text: str) -> str:
        # Keep this intentionally conservative.
        patterns = [
            r"(?:company|employer|at|for)\s+([A-Z][A-Za-z0-9&.\- ]{2,80})",
            r"([A-Z][A-Za-z0-9&.\- ]{2,80})\s+(?:is hiring|is looking|we are hiring)",
        ]
        invalid = {"you", "we", "they", "i", "it", "the", "a", "an", "and", "or"}
        for pat in patterns:
            m = re.search(pat, raw_text)
            if m:
                cand = m.group(1).strip().strip(".,:;()[]")
                if cand and cand.lower() not in invalid:
                    return cand
        return "Unknown"

    def _extract_role(self, text: str) -> str:
        patterns = [
            r"(?:role|position|title)[:\s]+([a-z0-9 \-/]{5,80})",
            r"(?:hiring|seeking)\s+(?:a|an)\s+([a-z0-9 \-/]{5,80})",
        ]
        for pat in patterns:
            m = re.search(pat, text)
            if m:
                cand = m.group(1).strip().strip(".,:;()[]")
                if any(k in cand for k in ["engineer", "developer", "manager", "analyst", "designer", "scientist"]):
                    return cand.title()
        return "Unknown"

    def _extract_section_skills(self, text: str, section_patterns: list[str]) -> list[str]:
        found: list[str] = []
        for pat in section_patterns:
            sections = re.findall(pat, text, re.DOTALL)
            for section in sections:
                found.extend(extract_skills(section, DEFAULT_SKILLS))
        # Dedup while preserving a stable sort.
        return sorted(set(found))

    def _fallback_keywords(self, text: str) -> list[str]:
        # When no known skills match, emit informative keywords rather than empty lists.
        stop = {
            "about",
            "this",
            "that",
            "with",
            "from",
            "your",
            "their",
            "they",
            "role",
            "the",
            "and",
            "for",
            "are",
            "you",
            "our",
            "we",
            "will",
            "to",
            "of",
            "in",
            "on",
            "a",
            "an",
            "as",
            "is",
            "be",
            "now",
            "looking",
        }
        words = re.findall(r"[a-z][a-z\-]{2,}", text)
        out: list[str] = []
        seen: set[str] = set()
        for w in words:
            if w in stop:
                continue
            if w in seen:
                continue
            seen.add(w)
            out.append(w)
            if len(out) >= 12:
                break
        return out or ["general"]

