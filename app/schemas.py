from pydantic import BaseModel, Field
from typing import Dict, List, Literal, Optional


class JobRequest(BaseModel):
    """Input model for job analysis endpoint."""
    job_description: str


class JobUrlRequest(BaseModel):
    url: str


class JobAnalysis(BaseModel):
    """Output model for job analysis."""
    company: str
    role: str
    must_have_skills: List[str]
    nice_to_have_skills: List[str]
    keywords: List[str]


class Preferences(BaseModel):
    tone: Literal["direct", "warm", "confident", "humble"] = "confident"
    focus: List[str] = Field(default_factory=list, description="Topics to emphasize, e.g. 'backend systems'.")
    max_cover_letter_paragraphs: int = Field(default=4, ge=2, le=8)


class ApplicationKitRequest(BaseModel):
    job_description: str
    resume_text: str
    preferences: Optional[Preferences] = None


class ApplicationKitFromUrlRequest(BaseModel):
    job_url: str
    resume_text: str
    preferences: Optional[Preferences] = None


class ResumeSummary(BaseModel):
    headline: str
    extracted_skills: List[str]
    key_bullets: List[str]


class MatchAnalysis(BaseModel):
    score: float = Field(ge=0.0, le=1.0)
    matched_must_haves: List[str]
    missing_must_haves: List[str]
    matched_nice_to_haves: List[str]
    suggested_resume_edits: List[str]


class AgentTraceItem(BaseModel):
    agent: str
    status: Literal["ok", "error"]
    output: Dict[str, object] = Field(default_factory=dict)
    error: Optional[str] = None


class ApplicationKitResponse(BaseModel):
    job: JobAnalysis
    resume: ResumeSummary
    match: MatchAnalysis
    cover_letter: str
    checklist: List[str]
    trace: List[AgentTraceItem]
