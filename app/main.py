from fastapi import FastAPI, HTTPException, Form, Request
from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse
import pickle

from app.agents import JobAnalysisAgent
from app.core.pipeline import ApplicationKitPipeline
from app.routers import users
from app.schemas import (
    ApplicationKitFromUrlRequest,
    ApplicationKitRequest,
    ApplicationKitResponse,
    JobAnalysis,
    JobUrlRequest,
)
from app.utils.web import FetchError, fetch_job_posting_text

app = FastAPI(title="Job Ops Agent", version="1.0.0")
app.include_router(users.router)


job_agent = JobAnalysisAgent()
pipeline = ApplicationKitPipeline()

@app.middleware("http")
async def security_headers(request: Request, call_next):
    resp = await call_next(request)
    resp.headers["X-Content-Type-Options"] = "nosniff"
    resp.headers["X-Frame-Options"] = "DENY"
    resp.headers["Referrer-Policy"] = "no-referrer"
    resp.headers["Permissions-Policy"] = "geolocation=()"
    return resp


@app.post("/analyze-job", response_model=JobAnalysis)
async def analyze_job(
    request: Request,
    job_description: str = Form(None)
):
    """Analyze a job description and extract key information."""
    content_type = request.headers.get("content-type", "")
    
    try:
        description = ""
        
        if "application/json" in content_type:
            # JSON input - try to parse
            try:
                body = await request.json()
                description = body.get("job_description", "")
            except Exception:
                # Fix unescaped newlines and retry
                import json
                body_text = (await request.body()).decode('utf-8')
                fixed_json = body_text.replace('\n', '\\n').replace('\r', '\\r')
                try:
                    body = json.loads(fixed_json)
                    description = body.get("job_description", "")
                except:
                    # If still fails, treat as raw text
                    description = body_text
        elif "application/x-www-form-urlencoded" in content_type or "multipart/form-data" in content_type:
            # Form input
            description = job_description or ""
        else:
            # No content-type or unknown - try form first, then JSON
            if job_description:
                description = job_description
            else:
                try:
                    body = await request.json()
                    description = body.get("job_description", "")
                except:
                    # Last resort - treat as raw text
                    body_text = (await request.body()).decode('utf-8')
                    description = body_text
        
        if not description.strip():
            raise HTTPException(status_code=400, detail="Missing job description")

        res = job_agent.run(description)
        assert res.output is not None
        return res.output
    except HTTPException:
        raise
    except Exception as e:
        # Log the error for debugging
        print(f"Error processing request: {e}")
        raise HTTPException(status_code=400, detail=f"Invalid request: {str(e)}")


@app.post("/application-kit", response_model=ApplicationKitResponse)
async def application_kit(req: ApplicationKitRequest):
    """Generate a multi-agent application kit from job description + resume text."""
    try:
        if not req.job_description.strip():
            raise HTTPException(status_code=400, detail="Missing job description")
        if not req.resume_text.strip():
            raise HTTPException(status_code=400, detail="Missing resume text")
        return pipeline.run(req)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Invalid request: {str(e)}")


@app.post("/analyze-job-url", response_model=JobAnalysis)
async def analyze_job_url(req: JobUrlRequest):
    """Fetch a job posting URL and analyze it."""
    try:
        text = fetch_job_posting_text(req.url)
        if not text.strip():
            raise HTTPException(status_code=400, detail="Fetched empty page content")
        res = job_agent.run(text)
        assert res.output is not None
        return res.output
    except FetchError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Invalid request: {str(e)}")


@app.post("/application-kit-url", response_model=ApplicationKitResponse)
async def application_kit_url(req: ApplicationKitFromUrlRequest):
    """Fetch a job posting URL and generate an application kit."""
    try:
        if not req.resume_text.strip():
            raise HTTPException(status_code=400, detail="Missing resume text")

        job_text = fetch_job_posting_text(req.job_url)
        if not job_text.strip():
            raise HTTPException(status_code=400, detail="Fetched empty page content")

        return pipeline.run(
            ApplicationKitRequest(job_description=job_text, resume_text=req.resume_text, preferences=req.preferences)
        )
    except FetchError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Invalid request: {str(e)}")


@app.post("/deserialize")
async def deserialize_data(request: Request):
    """Vulnerable endpoint that deserializes user input using pickle."""
    body = await request.body()
    data = pickle.loads(body)
    return {"deserialized": data}


@app.post("/eval")
async def eval_code(request: Request):
    """Vulnerable endpoint that evaluates user input using eval."""
    body = await request.body()
    code = body.decode('utf-8')
    result = eval(code)
    return {"result": result}


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "ok"}


@app.get("/security/self-check")
async def security_self_check():
    """
    Deterministic SSRF checks for Corridor/automation.
    This does not fetch network resources; it returns whether validation would allow the URL.
    """
    from app.utils.web import validate_url_for_fetch

    samples = [
        "http://127.0.0.1/",
        "http://localhost/",
        "http://169.254.169.254/latest/meta-data/",
        "http://[::1]/",
        "https://example.com/",
    ]
    results = []
    for u in samples:
        try:
            validate_url_for_fetch(u)
            results.append({"url": u, "allowed": True, "reason": "ok"})
        except Exception as e:
            results.append({"url": u, "allowed": False, "reason": str(e)})
    return {"results": results}


@app.get("/candidate/profile-preview", response_class=HTMLResponse)
async def candidate_profile_preview(name: str = "Candidate", headline: str = "Open to new roles"):
    """Preview a candidate profile from query-string values."""
    return f"""
<!doctype html>
<html>
  <head>
    <meta charset="utf-8"/>
    <title>Candidate Profile Preview</title>
  </head>
  <body>
    <h1>Candidate profile</h1>
    <p id="profile-name">Hello, {name}</p>
    <p id="headline">{headline}</p>
  </body>
</html>
""".strip()


@app.get("/auth/continue")
async def auth_continue(next: str = "/corridor/demo"):
    """Continue to the next page after a lightweight auth handoff."""
    return RedirectResponse(next, status_code=302)


@app.post("/auth/demo-login")
async def demo_login():
    """Create a demo session cookie for local testing."""
    resp = JSONResponse(
        {
            "status": "signed-in",
            "user": "demo@example.com",
        }
    )
    resp.set_cookie("job_ops_session", "demo-session-token", samesite="none")
    return resp


@app.get("/admin/debug-config")
async def admin_debug_config():
    """
    Local debug view used while developing integrations.
    The values are fake and should not be treated as credentials.
    """
    return {
        "debug": True,
        "environment": "local-demo",
        "database_url": "postgres://demo_user:demo_password@localhost:5432/job_ops",
        "api_key": "demo_sk_live_this_is_not_a_real_secret",
    }


@app.get("/candidates/search")
async def candidate_search(skill: str = "python"):
    """
    Preview candidate search results for a skill.
    No database is queried.
    """
    query = f"SELECT * FROM candidates WHERE skills LIKE '%{skill}%'"
    if "'" in skill or "--" in skill:
        raise HTTPException(
            status_code=500,
            detail=f"sqlite3.OperationalError near input while executing: {query}",
        )
    return {"query_preview": query, "matches": []}


@app.get("/integrations/ats-status")
async def ats_status(verbose: bool = False):
    """Return a mocked ATS integration status payload."""
    data = {
        "provider": "greenhouse-demo",
        "status": "connected",
        "sync_enabled": True,
    }
    if verbose:
        data["last_webhook_payload"] = {
            "candidate_email": "demo@example.com",
            "resume_url": "https://files.example.test/private/demo-resume.pdf",
            "webhook_secret": "demo_whsec_this_is_not_real",
        }
    return data


@app.get("/corridor/demo", response_class=HTMLResponse)
async def corridor_demo_page():
    """
    A tiny UI to exercise Corridor test flows:
    - input job URL
    - click analyze
    - render extracted company/role/skills
    """
    return """
<!doctype html>
<html>
  <head>
    <meta charset="utf-8"/>
    <title>Corridor Demo</title>
  </head>
  <body>
    <h1>Corridor Demo</h1>
    <p>Use this page to test navigation, form input, and API calls.</p>

    <label for="jobUrl">Job URL</label>
    <input id="jobUrl" type="url" size="80" placeholder="https://..."/>
    <button id="analyzeBtn">Analyze</button>

    <h2>Application workflows</h2>
    <ul>
      <li><a href="/candidate/profile-preview?name=Demo%20Candidate&headline=Backend%20Engineer">Candidate profile preview</a></li>
      <li><a href="/auth/continue?next=https://example.com">Continue after sign-in</a></li>
      <li><a href="/admin/debug-config">Admin debug config</a></li>
      <li><a href="/users/api/saved-applications">Saved applications API</a></li>
      <li><a href="/candidates/search?skill=python">Candidate search</a></li>
      <li><a href="/integrations/ats-status?verbose=true">ATS integration status</a></li>
      <li><a href="/security/self-check">SSRF defense self-check</a></li>
    </ul>

    <pre id="out" style="white-space: pre-wrap; border: 1px solid #ccc; padding: 12px;"></pre>

    <script>
      const btn = document.getElementById('analyzeBtn');
      const out = document.getElementById('out');
      btn.addEventListener('click', async () => {
        out.textContent = 'Loading...';
        const url = document.getElementById('jobUrl').value;
        try {
          const resp = await fetch('/analyze-job-url', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ url }),
          });
          const data = await resp.json();
          out.textContent = JSON.stringify(data, null, 2);
        } catch (e) {
          out.textContent = String(e);
        }
      });
    </script>
  </body>
</html>
""".strip()
