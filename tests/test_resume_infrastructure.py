"""Comprehensive tests for Resume Infrastructure, Sandboxed Compilation, OpenRouter, and R2 Storage

Proves:
(a) Valid master .tex with editable markers uploads successfully via POST /resumes
(b) Invalid .tex is rejected with a clear structured error (missing marker, unclosed/mismatched environments)
(c) Sandboxed compile service returns PDF for trivial valid .tex fixture
(d) OpenRouter wrapper falls back to model 2 when model 1 is mocked with rate-limit (429) error
(e) Calling generate_bullet with OPENROUTER_API_KEY unset returns clean 'disabled' result without raising
"""
import os
import sys
import tempfile
import subprocess
from pathlib import Path
from unittest.mock import MagicMock, AsyncMock, patch

import pytest
import pytest_asyncio
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy import select

# Ensure project root is in sys.path
PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

# Add compiler microservice to sys.path
COMPILER_SERVICE_DIR = PROJECT_ROOT / "services" / "latex-compiler"
if str(COMPILER_SERVICE_DIR) not in sys.path:
    sys.path.insert(0, str(COMPILER_SERVICE_DIR))

from backend.database import Base, get_db
from backend.models import User, Resume, LLMCall
from backend.auth import get_password_hash, create_access_token
from backend.api import app as backend_app
from backend.latex_validator import validate_latex_source
from backend.exceptions import ValidationError
from llm.openrouter_client import generate_bullet, BulletResult
from storage.r2_client import upload_pdf, delete_pdf

# Import compiler service
import compiler as latex_compiler_module
from main import app as compiler_app


# ── Database Fixtures ────────────────────────────────────────────────────────
TEST_DB_FILE = tempfile.NamedTemporaryFile(suffix="_resumes.db", delete=False).name
TEST_DB_URL = f"sqlite+aiosqlite:///{TEST_DB_FILE}"
test_engine = create_async_engine(TEST_DB_URL, connect_args={"check_same_thread": False})
TestSessionLocal = async_sessionmaker(bind=test_engine, class_=AsyncSession, expire_on_commit=False)


async def override_get_db():
    async with TestSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


@pytest_asyncio.fixture(autouse=True)
async def setup_db():
    """Reset schema and create a default test user."""
    backend_app.dependency_overrides[get_db] = override_get_db
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)


    async with TestSessionLocal() as session:
        user = User(
            email="developer@example.com",
            hashed_password=get_password_hash("password123"),
            role="admin",
            is_active=True
        )
        session.add(user)
        await session.commit()

    yield

    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


def get_auth_headers(email: str = "developer@example.com") -> dict:
    token = create_access_token(data={"sub": email, "role": "admin"})
    return {"Authorization": f"Bearer {token}"}


# ── Sample Fixtures ──────────────────────────────────────────────────────────
VALID_LATEX_SOURCE = r"""\documentclass{article}
\begin{document}
%-- AI:EDITABLE START --%
\begin{itemize}
    \item Developed high-throughput REST APIs in Python.
\end{itemize}
%-- AI:EDITABLE END --%
\end{document}
"""

TRIVIAL_LATEX_FIXTURE = r"""\documentclass{article}
\begin{document}
Hello World Test
\end{document}
"""

INVALID_LATEX_NO_MARKER = r"""\documentclass{article}
\begin{document}
Plain resume without any AI markers.
\end{document}
"""

INVALID_LATEX_UNCLOSED_ENV = r"""\documentclass{article}
\begin{document}
%-- AI:EDITABLE START --%
\begin{itemize}
    \item Missing closing itemize.
\end{document}
"""

INVALID_LATEX_MISMATCHED_ENV = r"""\documentclass{article}
\begin{document}
%-- AI:EDITABLE START --%
\begin{itemize}
    \item Mismatched environment.
\end{enumerate}
\end{document}
"""


# ── (a) Valid Master .tex Upload Test ─────────────────────────────────────────
@pytest.mark.asyncio
async def test_a_valid_master_tex_uploads_successfully():
    """(a) A valid master .tex with editable markers uploads successfully."""
    transport = ASGITransport(app=backend_app)
    headers = get_auth_headers()

    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # Test upload via JSON payload
        payload = {
            "label": "Master Resume v1",
            "latex_source": VALID_LATEX_SOURCE,
            "is_master": True
        }
        res = await client.post("/resumes", json=payload, headers=headers)
        assert res.status_code == 201, f"Failed with {res.text}"
        data = res.json()
        assert data["label"] == "Master Resume v1"
        assert data["is_master"] is True
        assert "%-- AI:EDITABLE START --%" in data["latex_source"]
        resume_id = data["id"]

        # Verify retrieved via GET /resumes
        list_res = await client.get("/resumes", headers=headers)
        assert list_res.status_code == 200
        list_data = list_res.json()
        assert list_data["total"] >= 1
        assert any(r["id"] == resume_id for r in list_data["items"])

        # Verify retrieved via GET /resumes/{id}
        get_res = await client.get(f"/resumes/{resume_id}", headers=headers)
        assert get_res.status_code == 200
        assert get_res.json()["id"] == resume_id

        # Also test upload via multipart form-data (file upload)
        files = {
            "file": ("backend_resume.tex", VALID_LATEX_SOURCE.encode("utf-8"), "application/x-tex")
        }
        data_fields = {"label": "Backend Focused v2", "is_master": "false"}
        form_res = await client.post("/resumes", files=files, data=data_fields, headers=headers)
        assert form_res.status_code == 201
        form_data = form_res.json()
        assert form_data["label"] == "Backend Focused v2"
        assert form_data["is_master"] is False


# ── (b) Invalid .tex Rejected With Clear Error ────────────────────────────────
@pytest.mark.asyncio
async def test_b_invalid_tex_is_rejected_with_clear_error():
    """(b) An invalid .tex is rejected with a clear error."""
    transport = ASGITransport(app=backend_app)
    headers = get_auth_headers()

    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # Case 1: Missing %-- AI:EDITABLE START --% marker
        res_no_marker = await client.post(
            "/resumes",
            json={"label": "No Marker", "latex_source": INVALID_LATEX_NO_MARKER, "is_master": False},
            headers=headers
        )
        assert res_no_marker.status_code in (400, 422)
        err_data = res_no_marker.json()
        assert "AI:EDITABLE START" in err_data.get("detail", "") or "AI:EDITABLE START" in str(err_data)

        # Case 2: Unclosed environment (\begin{itemize} without \end{itemize})
        res_unclosed = await client.post(
            "/resumes",
            json={"label": "Unclosed", "latex_source": INVALID_LATEX_UNCLOSED_ENV, "is_master": False},
            headers=headers
        )
        assert res_unclosed.status_code in (400, 422)
        err_unclosed = res_unclosed.json()
        assert "Unclosed LaTeX environment" in err_unclosed.get("detail", "") or "itemize" in str(err_unclosed)

        # Case 3: Mismatched environments (\begin{itemize} ... \end{enumerate})
        res_mismatch = await client.post(
            "/resumes",
            json={"label": "Mismatch", "latex_source": INVALID_LATEX_MISMATCHED_ENV, "is_master": False},
            headers=headers
        )
        assert res_mismatch.status_code in (400, 422)
        err_mismatch = res_mismatch.json()
        assert "Mismatched environment" in err_mismatch.get("detail", "") or "enumerate" in str(err_mismatch)

        # Case 4: Pure validator function verification
        with pytest.raises(ValidationError) as exc_info:
            validate_latex_source("")
        assert "cannot be empty" in str(exc_info.value)


# ── (c) Compile Service Returns PDF for Trivial Fixture ───────────────────────
@pytest.mark.asyncio
async def test_c_compile_service_returns_pdf_for_trivial_fixture():
    """(c) The compile service returns a PDF for a trivial valid .tex fixture."""
    transport = ASGITransport(app=compiler_app)

    # Mock subprocess runner to simulate Tectonic generating a valid PDF
    dummy_pdf_bytes = b"%PDF-1.4\n1 0 obj\n<< /Type /Catalog >>\nendobj\ntrailer\n<< >>\n%%EOF"

    def mock_subprocess_run(cmd, cwd, **kwargs):
        # Verify mandatory security constraints on CLI command
        assert "-C" in cmd or "--only-cached" in cmd, "Network access flag not disabled"
        assert "--untrusted" in cmd, "Untrusted mode flag missing"
        assert kwargs.get("env", {}).get("TECTONIC_UNTRUSTED_MODE") == "1", "TECTONIC_UNTRUSTED_MODE env missing"

        # Create simulated PDF in cwd
        pdf_out = os.path.join(cwd, "document.pdf")
        with open(pdf_out, "wb") as pf:
            pf.write(dummy_pdf_bytes)

        mock_res = MagicMock()
        mock_res.returncode = 0
        mock_res.stdout = "Tectonic compiled document.tex successfully"
        mock_res.stderr = ""
        return mock_res

    with patch.object(latex_compiler_module.subprocess, "run", side_effect=mock_subprocess_run):
        async with AsyncClient(transport=transport, base_url="http://compiler-service") as client:
            resp = await client.post(
                "/compile",
                json={"latex_source": TRIVIAL_LATEX_FIXTURE, "timeout_sec": 20}
            )
            assert resp.status_code == 200
            assert resp.headers.get("content-type") == "application/pdf"
            assert resp.content.startswith(b"%PDF-")
            assert len(resp.content) == len(dummy_pdf_bytes)

    # Verify compiler error handling on non-zero exit code
    def mock_subprocess_fail(cmd, cwd, **kwargs):
        mock_res = MagicMock()
        mock_res.returncode = 1
        mock_res.stdout = "! Undefined control sequence \\unknowncmd"
        mock_res.stderr = "Fatal error occurred"
        return mock_res

    with patch.object(latex_compiler_module.subprocess, "run", side_effect=mock_subprocess_fail):
        async with AsyncClient(transport=transport, base_url="http://compiler-service") as client:
            resp_fail = await client.post(
                "/compile",
                json={"latex_source": r"\begin{document}\unknowncmd\end{document}"}
            )
            assert resp_fail.status_code == 422
            data = resp_fail.json()
            assert data["status"] == "error"
            assert "Undefined control sequence" in data["log"]


# ── (d) OpenRouter Fallback When Model 1 Hits Rate Limit ─────────────────────
@pytest.mark.asyncio
async def test_d_openrouter_wrapper_falls_back_to_model_2_on_rate_limit():
    """(d) The OpenRouter wrapper falls back to model 2 when model 1's call is mocked to raise a rate-limit error."""
    mock_client = AsyncMock()

    model_1 = "primary/model-fast"
    model_2 = "fallback/model-smart"

    # Define mock response for model 1 (HTTP 429) and model 2 (HTTP 200)
    resp_429 = MagicMock()
    resp_429.status_code = 429
    resp_429.text = "Rate limit exceeded (429)"

    resp_200 = MagicMock()
    resp_200.status_code = 200
    resp_200.json.return_value = {
        "choices": [
            {
                "message": {
                    "role": "assistant",
                    "content": "• Architected high-throughput REST APIs with Java and Spring Boot, cutting P99 latency by 35%."
                }
            }
        ]
    }

    async def side_effect_post(url, headers, json, timeout):
        requested_model = json.get("model")
        if requested_model == model_1:
            return resp_429
        elif requested_model == model_2:
            return resp_200
        return MagicMock(status_code=500)

    mock_client.post.side_effect = side_effect_post

    async with TestSessionLocal() as session:
        result = await generate_bullet(
            snippet="Built REST APIs in Java",
            jd_text="Looking for a backend engineer proficient in Java, Spring Boot, and low latency",
            context="Fintech domain",
            api_key="sk-or-v1-mock-test-key",
            model_priority=[model_1, model_2],
            client=mock_client,
            db=session
        )

        # Must return the bullet content and serving model
        assert result.result is not None
        assert "Spring Boot" in result.result
        assert result.model == model_2

        # Verify llm_calls table recorded BOTH attempts
        stmt = select(LLMCall).order_by(LLMCall.id.asc())
        calls = (await session.execute(stmt)).scalars().all()
        assert len(calls) == 2, f"Expected 2 attempts logged, got {len(calls)}"

        # Attempt 1 (model_1) failed
        assert calls[0].model_used == model_1
        assert calls[0].success is False
        assert "429" in (calls[0].error_message or "")

        # Attempt 2 (model_2) succeeded
        assert calls[1].model_used == model_2
        assert calls[1].success is True
        assert calls[1].error_message is None


# ── (e) OpenRouter Clean 'Disabled' Result When API Key Unset ────────────────
@pytest.mark.asyncio
async def test_e_openrouter_unset_api_key_returns_clean_disabled():
    """(e) With OPENROUTER_API_KEY unset, calling generate_bullet returns a clean 'disabled' result rather than raising."""
    # Ensure api_key is empty/unset
    with patch.dict(os.environ, {"OPENROUTER_API_KEY": ""}, clear=False):
        result = await generate_bullet(
            snippet="Worked on databases",
            jd_text="Postgres SQL database engineer",
            context="Tech",
            api_key=""  # Explicitly empty
        )

        # Must return clean disabled result without raising
        assert result.result == "disabled"
        assert result.model is None
        assert result == "disabled"
        assert str(result) == "disabled"


# ── Additional: Cloudflare R2 Client & Resume Deletion ───────────────────────
def test_r2_client_upload_and_delete_operations():
    """Verify Cloudflare R2 client upload and delete functionality with mock S3 client."""
    mock_s3 = MagicMock()
    mock_s3.put_object.return_value = {"ETag": "12345"}
    mock_s3.delete_object.return_value = {"DeleteMarker": True}

    fake_pdf = b"%PDF-1.4 mock content"

    with patch("storage.r2_client._get_r2_credentials", return_value={
        "access_key": "fake_key",
        "secret_key": "fake_secret",
        "bucket": "job-resumes",
        "endpoint": "https://fake.r2.cloudflarestorage.com",
        "public_url": "https://cdn.example.com"
    }):
        # Upload
        url = upload_pdf(fake_pdf, "resumes/user1_master.pdf", s3_client=mock_s3)
        assert url == "https://cdn.example.com/resumes/user1_master.pdf"
        mock_s3.put_object.assert_called_once()

        # Delete
        deleted = delete_pdf("resumes/user1_master.pdf", s3_client=mock_s3)
        assert deleted is True
        mock_s3.delete_object.assert_called_once()

    # Unconfigured R2: Gracefully disables and returns None/False without crashing
    with patch("storage.r2_client._get_r2_credentials", return_value=None):
        url_disabled = upload_pdf(fake_pdf, "resumes/test.pdf")
        assert url_disabled is None

        del_disabled = delete_pdf("resumes/test.pdf")
        assert del_disabled is False


@pytest.mark.asyncio
async def test_delete_resume_endpoint():
    """Test DELETE /resumes/{id} deletes the resume record."""
    transport = ASGITransport(app=backend_app)
    headers = get_auth_headers()

    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # Create resume
        post_r = await client.post(
            "/resumes",
            json={"label": "To Be Deleted", "latex_source": VALID_LATEX_SOURCE, "is_master": False},
            headers=headers
        )
        assert post_r.status_code == 201
        res_id = post_r.json()["id"]

        # Delete resume
        del_r = await client.delete(f"/resumes/{res_id}", headers=headers)
        assert del_r.status_code == 200

        # Verify 404 on get
        get_r = await client.get(f"/resumes/{res_id}", headers=headers)
        assert get_r.status_code == 404
