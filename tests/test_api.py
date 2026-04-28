import pytest
from fastapi.testclient import TestClient
from app.main import app


client = TestClient(app)


class TestAnalyzeJob:
    """Tests for the /analyze-job endpoint."""

    def test_analyze_job_basic(self):
        """Test basic job analysis."""
        payload = {
            "job_description": "Role: Senior Python Developer. Company: TechCorp. "
                              "Required skills: Python, Django, PostgreSQL. "
                              "Nice to have: Docker, Kubernetes."
        }
        response = client.post("/analyze-job", json=payload)
        
        assert response.status_code == 200
        data = response.json()
        assert "company" in data
        assert "role" in data
        assert "must_have_skills" in data
        assert "nice_to_have_skills" in data
        assert "keywords" in data

    def test_analyze_job_response_structure(self):
        """Test response has correct structure and types."""
        payload = {
            "job_description": "Position: Junior Developer at StartupX. "
                              "Required: JavaScript, React. Nice: TypeScript."
        }
        response = client.post("/analyze-job", json=payload)
        
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data["company"], str)
        assert isinstance(data["role"], str)
        assert isinstance(data["must_have_skills"], list)
        assert isinstance(data["nice_to_have_skills"], list)
        assert isinstance(data["keywords"], list)

    def test_analyze_job_missing_description(self):
        """Test error handling for missing job description."""
        response = client.post("/analyze-job", json={})
        assert response.status_code == 400  # Bad requestt error

    def test_health_check(self):
        """Test health check endpoint."""
        response = client.get("/health")
        assert response.status_code == 200
        assert response.json()["status"] == "ok"

    def test_analyze_job_with_keywords(self):
        """Test keyword extraction."""
        payload = {
            "job_description": "Seeking Python and JavaScript developer with Docker "
                              "and Kubernetes experience. Python is required."
        }
        response = client.post("/analyze-job", json=payload)
        
        assert response.status_code == 200
        data = response.json()
        # Should extract Python and JavaScript
        keywords = data["keywords"]
        assert "python" in keywords

    def test_analyze_job_comprehensive(self):
        """Test comprehensive job analysis with non-empty skills and keywords."""
        payload = {
            "job_description": "About this role\nWhy Hightouch, Why Now\n\nMore than 1,000 enterprises use Hightouch to run their marketing. We launched the Agentic Marketing Platform.\n\nThe Role\nFounding PM for Agentic Personalization: Hightouch's third major pillar. You define the product and go-to-market strategy.\n\nWhat We're Looking For\nZero-to-one track record. Products you built from nothing to meaningful revenue, ideally at a B2B SaaS company.\n\nTechnical depth. Can evaluate architectural tradeoffs and debate infrastructure decisions.\n\nCommercial instinct. Think in terms of pipeline and conversion.\n\nCross-functional trust. This spans engineering, design, sales, and leadership."
        }
        response = client.post("/analyze-job", json=payload)
        
        assert response.status_code == 200
        data = response.json()
        
        # Verify response shape
        assert "company" in data
        assert "role" in data
        assert "must_have_skills" in data
        assert "nice_to_have_skills" in data
        assert "keywords" in data
        
        # Verify must_have_skills is non-empty
        assert len(data["must_have_skills"]) > 0
        assert isinstance(data["must_have_skills"], list)
        
        # Verify keywords is non-empty
        assert len(data["keywords"]) > 0
        assert isinstance(data["keywords"], list)
        
        # Verify some expected skills are extracted
        keywords = data["keywords"]
        assert any(skill in keywords for skill in ["product management", "b2b", "saas", "strategy"])

    def test_analyze_job_plain_text(self):
        """Test job analysis with plain text input."""
        job_text = """About this role
Why Hightouch, Why Now

More than 1,000 enterprises use Hightouch to run their marketing.

The Role
Founding PM for Agentic Personalization: Hightouch's third major pillar.

What We're Looking For
Zero-to-one track record. Products you built from nothing to meaningful revenue.
Technical depth. Can evaluate architectural tradeoffs.
Commercial instinct. Think in terms of pipeline and conversion."""

        response = client.post("/analyze-job", data={"job_description": job_text})
        
        assert response.status_code == 200
        data = response.json()
        
        # Verify response shape
        assert "company" in data
        assert "role" in data
        assert "must_have_skills" in data
        assert "nice_to_have_skills" in data
        assert "keywords" in data
        
        # Verify must_have_skills is non-empty
        assert len(data["must_have_skills"]) > 0
        
        # Verify keywords is non-empty
        assert len(data["keywords"]) > 0

    def test_analyze_job_malformed_json(self):
        """Test job analysis with malformed JSON containing unescaped newlines."""
        # This simulates what happens when users paste multi-line text into JSON fields
        malformed_json = '''{
  "job_description": "About this role
Why Hightouch, Why Now

More than 1,000 enterprises use Hightouch.

The Role
Founding PM for Agentic Personalization."
}'''
        
        # Send as raw data to simulate malformed JSON
        response = client.post("/analyze-job", 
                             data=malformed_json,
                             headers={"Content-Type": "application/json"})
        
        assert response.status_code == 200
        data = response.json()
        
        # Verify response shape
        assert "company" in data
        assert "role" in data
        assert "must_have_skills" in data
        assert "nice_to_have_skills" in data
        assert "keywords" in data
        
        # Verify the job description was processed (should extract some skills)
        assert len(data["keywords"]) > 0


class TestApplicationKit:
    """Tests for the /application-kit endpoint."""

    def test_application_kit_basic(self):
        payload = {
            "job_description": "We are hiring a Senior Backend Engineer. Required: Python, FastAPI, Postgres, AWS. Nice: Kubernetes.",
            "resume_text": "Senior Backend Engineer\n- Built APIs with Python and FastAPI\n- Operated Postgres on AWS\nSkills: Python, FastAPI, Postgres, AWS, Docker",
            "preferences": {"tone": "direct", "focus": ["backend systems", "reliability"]},
        }
        response = client.post("/application-kit", json=payload)
        assert response.status_code == 200

        data = response.json()
        assert "job" in data
        assert "resume" in data
        assert "match" in data
        assert "cover_letter" in data
        assert "checklist" in data
        assert "trace" in data

        assert isinstance(data["cover_letter"], str)
        assert len(data["cover_letter"]) > 20
        assert isinstance(data["checklist"], list)
        assert isinstance(data["trace"], list)

        assert 0.0 <= data["match"]["score"] <= 1.0
        assert "python" in data["job"]["keywords"]

    def test_application_kit_missing_fields(self):
        response = client.post("/application-kit", json={"job_description": "x", "resume_text": ""})
        assert response.status_code == 400


class TestUrlEndpoints:
    def test_analyze_job_url_fetches_and_analyzes(self, monkeypatch):
        class FakeHttpResponse:
            status = 200

            def __init__(self, body: bytes):
                self._body = body
                self.headers = {"Content-Type": "text/html; charset=utf-8"}

            def read(self, n: int = -1):
                if n is None or n < 0:
                    return self._body
                return self._body[:n]

            def __enter__(self):
                return self

            def __exit__(self, exc_type, exc, tb):
                return False

        def fake_urlopen(req, timeout=15.0):
            return FakeHttpResponse(
                b"<html><body><h1>Role: Senior Backend Engineer</h1><p>Required: Python, FastAPI, Postgres.</p></body></html>"
            )

        import urllib.request

        monkeypatch.setattr(urllib.request, "urlopen", fake_urlopen)
        import socket

        monkeypatch.setattr(
            socket,
            "getaddrinfo",
            lambda host, port=None: [(socket.AF_INET, None, None, None, ("93.184.216.34", 0))],
        )

        response = client.post("/analyze-job-url", json={"url": "https://example.com/job"})
        assert response.status_code == 200
        data = response.json()
        assert len(data["keywords"]) > 0

    def test_application_kit_url_fetches_and_runs_pipeline(self, monkeypatch):
        class FakeHttpResponse:
            status = 200

            def __init__(self, body: bytes):
                self._body = body
                self.headers = {"Content-Type": "text/html; charset=utf-8"}

            def read(self, n: int = -1):
                if n is None or n < 0:
                    return self._body
                return self._body[:n]

            def __enter__(self):
                return self

            def __exit__(self, exc_type, exc, tb):
                return False

        def fake_urlopen(req, timeout=15.0):
            return FakeHttpResponse(b"<html><body><p>Required: Python, FastAPI, Postgres.</p><p>Nice: AWS.</p></body></html>")

        import urllib.request

        monkeypatch.setattr(urllib.request, "urlopen", fake_urlopen)
        import socket

        monkeypatch.setattr(
            socket,
            "getaddrinfo",
            lambda host, port=None: [(socket.AF_INET, None, None, None, ("93.184.216.34", 0))],
        )

        response = client.post(
            "/application-kit-url",
            json={
                "job_url": "https://example.com/job",
                "resume_text": "Skills: Python, FastAPI, Postgres, AWS",
                "preferences": {"tone": "warm"},
            },
        )
        assert response.status_code == 200
        data = response.json()
        assert "cover_letter" in data
        assert 0.0 <= data["match"]["score"] <= 1.0

    def test_security_self_check_endpoint(self):
        resp = client.get("/security/self-check")
        assert resp.status_code == 200
        data = resp.json()
        assert "results" in data
        assert any(item["allowed"] is False for item in data["results"])


class TestSecurityScanTargets:
    def test_corridor_demo_page_links_to_application_workflows(self):
        resp = client.get("/corridor/demo")
        assert resp.status_code == 200
        assert "Application workflows" in resp.text
        assert "/candidate/profile-preview" in resp.text
        assert "/admin/debug-config" in resp.text

    def test_candidate_profile_preview_renders_unescaped_input(self):
        payload = "<script>alert(1)</script>"
        resp = client.get("/candidate/profile-preview", params={"name": payload})
        assert resp.status_code == 200
        assert payload in resp.text

    def test_auth_continue_uses_user_controlled_redirect_target(self):
        resp = client.get(
            "/auth/continue",
            params={"next": "https://example.com"},
            follow_redirects=False,
        )
        assert resp.status_code == 302
        assert resp.headers["location"] == "https://example.com"

    def test_demo_login_sets_weak_cookie(self):
        resp = client.post("/auth/demo-login")
        assert resp.status_code == 200
        cookie = resp.headers["set-cookie"]
        assert "job_ops_session=demo-session-token" in cookie
        assert "HttpOnly" not in cookie
        assert "Secure" not in cookie
        assert "SameSite=none" in cookie

    def test_admin_debug_config_exposes_demo_secret_values(self):
        resp = client.get("/admin/debug-config")
        assert resp.status_code == 200
        data = resp.json()
        assert data["debug"] is True
        assert "demo_password" in data["database_url"]
        assert data["api_key"].startswith("demo_sk_live_")

    def test_candidate_search_returns_verbose_error(self):
        resp = client.get("/candidates/search", params={"skill": "python'"})
        assert resp.status_code == 500
        assert "sqlite3.OperationalError" in resp.json()["detail"]

    def test_ats_status_verbose_exposes_integration_details(self):
        resp = client.get("/integrations/ats-status", params={"verbose": True})
        assert resp.status_code == 200
        data = resp.json()
        assert data["last_webhook_payload"]["candidate_email"] == "demo@example.com"
        assert data["last_webhook_payload"]["webhook_secret"].startswith("demo_whsec_")

    def test_current_user_dependency_rejects_missing_authentication(self):
        resp = client.get("/users/api/me")
        assert resp.status_code == 401
        assert resp.json()["detail"] == "Missing authentication token"

    def test_current_user_dependency_accepts_demo_token(self):
        resp = client.get("/users/api/me", headers={"Authorization": "Bearer demo-valid-token"})
        assert resp.status_code == 200
        assert resp.json()["email"] == "demo@example.com"

    def test_saved_applications_route_is_missing_authentication(self):
        resp = client.get("/users/api/saved-applications")
        assert resp.status_code == 200
        assert resp.json()["owner"] == "demo@example.com"
