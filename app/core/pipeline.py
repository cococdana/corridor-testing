from __future__ import annotations

from typing import List, Tuple

from app.agents import (
    ChecklistAgent,
    CoverLetterAgent,
    JobAnalysisAgent,
    MatcherAgent,
    ResumeSummaryAgent,
)
from app.schemas import (
    AgentTraceItem,
    ApplicationKitRequest,
    ApplicationKitResponse,
    JobAnalysis,
    MatchAnalysis,
    ResumeSummary,
)


class ApplicationKitPipeline:
    def __init__(self) -> None:
        self.job_agent = JobAnalysisAgent()
        self.resume_agent = ResumeSummaryAgent()
        self.matcher = MatcherAgent()
        self.cover_letter = CoverLetterAgent()
        self.checklist = ChecklistAgent()

    def run(self, req: ApplicationKitRequest) -> ApplicationKitResponse:
        trace: List[AgentTraceItem] = []

        job, trace = self._run_job(req, trace)
        resume, trace = self._run_resume(req, trace)
        match, trace = self._run_match(job, resume, trace)
        letter, trace = self._run_letter(job, resume, match, req, trace)
        checklist, trace = self._run_checklist(job, match, trace)

        return ApplicationKitResponse(
            job=job,
            resume=resume,
            match=match,
            cover_letter=letter,
            checklist=checklist,
            trace=trace,
        )

    def _run_job(self, req: ApplicationKitRequest, trace: List[AgentTraceItem]) -> Tuple[JobAnalysis, List[AgentTraceItem]]:
        try:
            res = self.job_agent.run(req.job_description)
            assert res.output is not None
            trace.append(AgentTraceItem(agent=res.agent, status="ok", output=res.output.model_dump()))
            return res.output, trace
        except Exception as e:
            trace.append(AgentTraceItem(agent=self.job_agent.name, status="error", output={}, error=str(e)))
            raise

    def _run_resume(
        self, req: ApplicationKitRequest, trace: List[AgentTraceItem]
    ) -> Tuple[ResumeSummary, List[AgentTraceItem]]:
        try:
            res = self.resume_agent.run(req.resume_text)
            assert res.output is not None
            trace.append(AgentTraceItem(agent=res.agent, status="ok", output=res.output.model_dump()))
            return res.output, trace
        except Exception as e:
            trace.append(AgentTraceItem(agent=self.resume_agent.name, status="error", output={}, error=str(e)))
            raise

    def _run_match(
        self, job: JobAnalysis, resume: ResumeSummary, trace: List[AgentTraceItem]
    ) -> Tuple[MatchAnalysis, List[AgentTraceItem]]:
        try:
            res = self.matcher.run(job, resume)
            assert res.output is not None
            trace.append(AgentTraceItem(agent=res.agent, status="ok", output=res.output.model_dump()))
            return res.output, trace
        except Exception as e:
            trace.append(AgentTraceItem(agent=self.matcher.name, status="error", output={}, error=str(e)))
            raise

    def _run_letter(
        self,
        job: JobAnalysis,
        resume: ResumeSummary,
        match: MatchAnalysis,
        req: ApplicationKitRequest,
        trace: List[AgentTraceItem],
    ) -> Tuple[str, List[AgentTraceItem]]:
        try:
            res = self.cover_letter.run(job, resume, match, req.preferences)
            assert res.output is not None
            trace.append(AgentTraceItem(agent=res.agent, status="ok", output={"cover_letter": res.output}))
            return res.output, trace
        except Exception as e:
            trace.append(AgentTraceItem(agent=self.cover_letter.name, status="error", output={}, error=str(e)))
            raise

    def _run_checklist(
        self, job: JobAnalysis, match: MatchAnalysis, trace: List[AgentTraceItem]
    ) -> Tuple[list[str], List[AgentTraceItem]]:
        try:
            res = self.checklist.run(job, match)
            assert res.output is not None
            trace.append(AgentTraceItem(agent=res.agent, status="ok", output={"checklist": res.output}))
            return res.output, trace
        except Exception as e:
            trace.append(AgentTraceItem(agent=self.checklist.name, status="error", output={}, error=str(e)))
            raise

