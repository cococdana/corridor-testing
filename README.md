## Job Application Multi-Agent (FastAPI)

A small **multi-agent** Python project for building a job application “kit” from:

- a job description
- your resume (paste as text)
- optional preferences (tone, focus areas)

It’s intentionally rule-based (no external LLM dependency) so it runs offline and is easy to extend with your own LLM/agents later.

### What you get

- **Job analysis agent**: extracts company/role + required/nice-to-have skills
- **Resume summarizer agent**: extracts your key skills + experience bullets
- **Matcher agent**: computes a match score + gap analysis
- **Cover letter agent**: drafts a tailored cover letter
- **Checklist agent**: creates a submission checklist (attachments + follow-ups)
- **Trace**: per-agent outputs so you can debug/iterate

### Run locally

Create/activate a virtualenv, then:

```bash
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```

Open `http://127.0.0.1:8000/docs`.

### Example request

```bash
curl -s http://127.0.0.1:8000/application-kit \
  -H 'Content-Type: application/json' \
  -d '{
    "job_description": "We are hiring a Senior Backend Engineer with Python, FastAPI, Postgres, AWS. Nice: Kubernetes.",
    "resume_text": "Senior software engineer... Skills: Python, FastAPI, Postgres, AWS, Docker. Led API modernization...",
    "preferences": { "tone": "direct", "focus": ["backend systems", "reliability"] }
  }' | python -m json.tool
```

### Run tests

```bash
pytest -q
```

