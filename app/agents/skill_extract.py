from __future__ import annotations

import re
from typing import Iterable, List, Set


DEFAULT_SKILLS: Set[str] = {
    # Programming languages
    "python",
    "javascript",
    "typescript",
    "java",
    "go",
    "rust",
    "c++",
    "c#",
    "php",
    "ruby",
    "scala",
    # Frontend
    "react",
    "angular",
    "vue",
    "svelte",
    "html",
    "css",
    "scss",
    "tailwind",
    # Backend
    "node",
    "nodejs",
    "express",
    "fastapi",
    "django",
    "flask",
    # Cloud & DevOps
    "aws",
    "gcp",
    "azure",
    "docker",
    "kubernetes",
    "terraform",
    "jenkins",
    "gitlab",
    "github",
    "ci/cd",
    # Databases
    "sql",
    "postgresql",
    "postgres",
    "mysql",
    "mongodb",
    "redis",
    "elasticsearch",
    # APIs & Web
    "rest",
    "api",
    "graphql",
    "sdk",
    "webhook",
    # PM & Business skills
    "product management",
    "product manager",
    "roadmap",
    "strategy",
    "b2b",
    "saas",
    "go-to-market",
    "gtm",
    "customer discovery",
    "user research",
    "analytics",
    "data analysis",
    "ml",
    "machine learning",
    "agile",
    "scrum",
    "cross-functional",
    "communication",
    "leadership",
    "negotiation",
}


def normalize_text(text: str) -> str:
    return re.sub(r"\s+", " ", text.strip()).lower()


def extract_skills(text: str, skills: Iterable[str] = DEFAULT_SKILLS) -> List[str]:
    t = normalize_text(text)
    found = [s for s in skills if s in t]
    return sorted(set(found))


def extract_bullets(text: str, max_items: int = 8) -> List[str]:
    lines = [ln.strip() for ln in text.splitlines()]
    bullets: List[str] = []
    for ln in lines:
        if re.match(r"^(\-|\*|•)\s+\S", ln):
            bullets.append(re.sub(r"^(\-|\*|•)\s+", "", ln).strip())
        elif re.match(r"^\d+\.\s+\S", ln):
            bullets.append(re.sub(r"^\d+\.\s+", "", ln).strip())
        if len(bullets) >= max_items:
            break
    return bullets

