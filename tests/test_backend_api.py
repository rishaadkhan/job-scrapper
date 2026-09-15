"""Comprehensive test suite for FastAPI backend service, auth, CRUD, exports, and retention"""
import os
import tempfile
import pytest
import pytest_asyncio
from unittest.mock import patch, AsyncMock
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker

from backend.database import Base, get_db
from backend.models import User, Company, Job, FilterConfig, ExportRecord, ScrapeRun
from backend.auth import get_password_hash, create_access_token
from backend.api import app
from backend.retention import run_retention_purge

# Test Database setup in temp file
TEST_DB_FILE = tempfile.NamedTemporaryFile(suffix=".db", delete=False).name
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


app.dependency_overrides[get_db] = override_get_db


@pytest_asyncio.fixture(autouse=True)
async def setup_db():
    """Create fresh schema and seed admin user & test data before each test."""
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)

    async with TestSessionLocal() as session:
        # 1. Admin user
        admin = User(
            email="admin@test.com",
            hashed_password=get_password_hash("password123"),
            role="admin",
            is_active=True
        )
        session.add(admin)

        # 2. Viewer user
        viewer = User(
            email="viewer@test.com",
            hashed_password=get_password_hash("viewer123"),
            role="viewer",
            is_active=True
        )
        session.add(viewer)

        # 3. Companies
        c1 = Company(
            name="Stripe",
            career_url="https://boards-api.greenhouse.io/v1/boards/stripe/jobs",
            ats="greenhouse",
            ats_token="stripe",
            location_filter=["India", "Bangalore"],
            active=True
        )
        c2 = Company(
            name="Stripe India",
            career_url="https://boards-api.greenhouse.io/v1/boards/stripe/jobs",
            ats="greenhouse",
            ats_token="stripe",
            location_filter=["India"],
            active=True
        )
        session.add_all([c1, c2])

        # 4. FilterConfig
        f = FilterConfig(
            name="default",
            is_active=True,
            target_locations=["bangalore", "hyderabad", "india"],
            backend_keywords=["software engineer", "backend engineer"],
            exclude_keywords=["senior", "staff"],
            tech_stack_keywords=["java", "python", "spring boot"],
            min_experience=0,
            max_experience=3,
            llm_suggestion_threshold=60
        )
        session.add(f)

        # 5. Jobs
        j1 = Job(
            job_id="Stripe_1001",
            company_name="Stripe",
            title="Software Engineer, Backend",
            match_score=85,
            experience_range="1-3 years",
            location="Bengaluru, India",
            top_jd_keywords=["Java", "Spring Boot", "Kafka"],
            missing_from_resume=["Kafka"],
            suggested_bullets="Architected distributed Kafka queues",
            description="Looking for a backend engineer with Java and Kafka",
            apply_link="https://stripe.com/jobs/1001",
            portal_url="https://stripe.com/careers"
        )
        j2 = Job(
            job_id="Stripe_1002",
            company_name="Stripe",
            title="Systems Engineer",
            match_score=45,
            experience_range="0-2 years",
            location="Bengaluru, India",
            top_jd_keywords=["Go", "Linux"],
            missing_from_resume=["Go"],
            description="Systems engineer role",
            apply_link="https://stripe.com/jobs/1002",
            portal_url="https://stripe.com/careers"
        )
        session.add_all([j1, j2])
        await session.commit()

    yield

    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


@pytest.mark.asyncio
async def test_health_and_root():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        r = await client.get("/")
        assert r.status_code == 200
        assert r.json()["service"] == "Job Scraper Enterprise API"

        r = await client.get("/health")
        assert r.status_code == 200
        assert r.json()["status"] == "healthy"


@pytest.mark.asyncio
async def test_auth_login_and_me():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # Invalid credentials
        r = await client.post("/auth/login", json={"email": "admin@test.com", "password": "wrongpassword"})
        assert r.status_code == 401
        assert r.json()["error_code"] == "AUTHENTICATION_FAILED"

        # Valid login
        r = await client.post("/auth/login", json={"email": "admin@test.com", "password": "password123"})
        assert r.status_code == 200
        data = r.json()
        assert "access_token" in data
        assert data["role"] == "admin"
        assert data["email"] == "admin@test.com"

        token = data["access_token"]
        headers = {"Authorization": f"Bearer {token}"}

        # Protected /auth/me
        r = await client.get("/auth/me", headers=headers)
        assert r.status_code == 200
        assert r.json()["email"] == "admin@test.com"


@pytest.mark.asyncio
async def test_companies_crud_and_dedup_warning():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # Login as admin
        r = await client.post("/auth/login", json={"email": "admin@test.com", "password": "password123"})
        token = r.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}

        # List companies (check dedup warnings)
        r = await client.get("/companies", headers=headers)
        assert r.status_code == 200
        data = r.json()
        assert data["total"] == 2
        assert len(data["dedup_warnings"]) >= 1
        assert "Stripe India" in data["dedup_warnings"][0] or "Stripe" in data["dedup_warnings"][0]

        # Add new company
        r = await client.post("/companies", headers=headers, json={
            "name": "Razorpay",
            "career_url": "https://api.lever.co/v0/postings/razorpay?mode=json",
            "ats": "lever",
            "ats_token": "razorpay",
            "location_filter": ["India", "Bengaluru"]
        })
        assert r.status_code == 201
        new_comp_id = r.json()["id"]

        # Duplicate company name error
        r = await client.post("/companies", headers=headers, json={
            "name": "Razorpay",
            "career_url": "https://example.com",
            "ats": "generic"
        })
        assert r.status_code == 409
        assert r.json()["error_code"] == "CONFLICT"

        # Edit company
        r = await client.put(f"/companies/{new_comp_id}", headers=headers, json={
            "company_type": "Unicorn"
        })
        assert r.status_code == 200
        assert r.json()["company_type"] == "Unicorn"

        # Deactivate company
        r = await client.delete(f"/companies/{new_comp_id}", headers=headers)
        assert r.status_code == 200


@pytest.mark.asyncio
async def test_filters_api():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # Login
        r = await client.post("/auth/login", json={"email": "admin@test.com", "password": "password123"})
        token = r.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}

        # Get filters
        r = await client.get("/filters", headers=headers)
        assert r.status_code == 200
        assert "bangalore" in r.json()["target_locations"]
        assert r.json()["max_experience"] == 3

        # Update filters
        r = await client.put("/filters", headers=headers, json={
            "max_experience": 2,
            "llm_suggestion_threshold": 75
        })
        assert r.status_code == 200
        assert r.json()["max_experience"] == 2
        assert r.json()["llm_suggestion_threshold"] == 75


@pytest.mark.asyncio
async def test_jobs_and_stats_api():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # Login
        r = await client.post("/auth/login", json={"email": "admin@test.com", "password": "password123"})
        token = r.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}

        # List all jobs
        r = await client.get("/jobs", headers=headers)
        assert r.status_code == 200
        data = r.json()
        assert data["total"] == 2
        assert data["items"][0]["match_score"] == 85  # ordered desc

        # Filter by min_score
        r = await client.get("/jobs?min_score=70", headers=headers)
        assert r.status_code == 200
        assert r.json()["total"] == 1
        assert r.json()["items"][0]["job_id"] == "Stripe_1001"

        # Get job stats
        r = await client.get("/jobs/stats", headers=headers)
        assert r.status_code == 200
        stats = r.json()
        assert stats["total_leads"] == 2
        assert stats["high_match_count"] == 1
        assert stats["mid_match_count"] == 1
        assert stats["low_match_count"] == 0

        # Get job detail
        job_id = data["items"][0]["id"]
        r = await client.get(f"/jobs/{job_id}", headers=headers)
        assert r.status_code == 200
        assert r.json()["title"] == "Software Engineer, Backend"


@pytest.mark.asyncio
async def test_exports_and_downloads():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # Login
        r = await client.post("/auth/login", json={"email": "admin@test.com", "password": "password123"})
        token = r.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}

        # Trigger export generation
        r = await client.post("/exports", headers=headers, json={"min_score": 0})
        assert r.status_code == 201
        exp_data = r.json()
        assert exp_data["row_count"] == 2
        assert exp_data["avg_match_score"] == 65.0
        export_id = exp_data["id"]

        # List exports
        r = await client.get("/exports", headers=headers)
        assert r.status_code == 200
        assert len(r.json()["items"]) >= 1

        # Download export
        r = await client.get(f"/exports/{export_id}/download", headers=headers)
        assert r.status_code == 200
        assert r.headers["content-type"] == "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"

        # Delete export
        r = await client.delete(f"/exports/{export_id}", headers=headers)
        assert r.status_code == 200


@pytest.mark.asyncio
async def test_runs_and_trigger():
    transport = ASGITransport(app=app)
    with patch("backend.routers.runs.run_scraper_task", new_callable=AsyncMock) as mock_task:
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            # Login
            r = await client.post("/auth/login", json={"email": "admin@test.com", "password": "password123"})
            token = r.json()["access_token"]
            headers = {"Authorization": f"Bearer {token}"}

            # List runs
            r = await client.get("/runs", headers=headers)
            assert r.status_code == 200

            # Trigger run
            r = await client.post("/runs/trigger", headers=headers)
            assert r.status_code == 202
            assert r.json()["status"] == "running"


@pytest.mark.asyncio
async def test_rbac_viewer_restrictions():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # Login as viewer
        r = await client.post("/auth/login", json={"email": "viewer@test.com", "password": "viewer123"})
        assert r.status_code == 200
        viewer_token = r.json()["access_token"]
        viewer_headers = {"Authorization": f"Bearer {viewer_token}"}

        # Viewer CAN read jobs and companies
        r = await client.get("/jobs", headers=viewer_headers)
        assert r.status_code == 200

        r = await client.get("/companies", headers=viewer_headers)
        assert r.status_code == 200

        # Viewer CANNOT add companies (requires admin)
        r = await client.post("/companies", headers=viewer_headers, json={
            "name": "Unauthorized Company",
            "career_url": "https://test.com"
        })
        assert r.status_code == 403
        assert r.json()["error_code"] == "FORBIDDEN"

        # Viewer CANNOT modify filters (requires admin)
        r = await client.put("/filters", headers=viewer_headers, json={"max_experience": 5})
        assert r.status_code == 403
        assert r.json()["error_code"] == "FORBIDDEN"


@pytest.mark.asyncio
async def test_retention_purge_dry_run():
    # Test retention function in dry-run mode
    summary = await run_retention_purge(days=0, dry_run=True)
    assert summary["dry_run"] is True
    assert "purged_count" in summary
