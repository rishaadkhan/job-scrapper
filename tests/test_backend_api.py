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


@pytest_asyncio.fixture(autouse=True)
async def setup_db():
    """Create fresh schema and seed admin user & test data before each test."""
    app.dependency_overrides[get_db] = override_get_db
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

        # Download export via header
        r = await client.get(f"/exports/{export_id}/download", headers=headers)
        assert r.status_code == 200
        assert r.headers["content-type"] == "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"

        # Download export via query parameter token
        r_query = await client.get(f"/exports/{export_id}/download?token={token}")
        assert r_query.status_code == 200
        assert r_query.headers["content-type"] == "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"

        # Unauthenticated download without header or query token should be 401
        r_unauth = await client.get(f"/exports/{export_id}/download")
        assert r_unauth.status_code == 401

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

            # Concurrent trigger attempt while run is in progress should return 409 Conflict
            r_conflict = await client.post("/runs/trigger", headers=headers)
            assert r_conflict.status_code == 409
            assert "already in progress" in r_conflict.json()["detail"].lower()


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


@pytest.mark.asyncio
async def test_db_save_scrape_results_with_run_id():
    """Verify that passing an existing run_id updates the run rather than duplicating it."""
    from backend.db_service import db_save_scrape_results
    from datetime import datetime, timezone
    from sqlalchemy import select

    async with TestSessionLocal() as session:
        # Create an initial running ScrapeRun
        init_run = ScrapeRun(status="running", started_at=datetime.now(timezone.utc).replace(tzinfo=None))
        session.add(init_run)
        await session.commit()
        await session.refresh(init_run)
        run_id = init_run.id

    valid_jobs = [{
        "company": "Acme Corp",
        "title": "Backend Python Engineer",
        "job_id": "acme-123",
        "match_score": 85,
        "location": "Bengaluru",
        "description": "Python, FastAPI, Postgres"
    }]
    company_stats = [{
        "company": "Acme Corp",
        "raw_count": 5,
        "valid_count": 1
    }]

    with patch("backend.db_service.AsyncSessionLocal", TestSessionLocal):
        res_run_id = await db_save_scrape_results(
            valid_jobs=valid_jobs,
            company_stats=company_stats,
            start_time_dt=datetime.now(timezone.utc).replace(tzinfo=None),
            duration_sec=12.5,
            run_id=run_id
        )

    assert res_run_id == run_id

    async with TestSessionLocal() as session:
        # Verify the same run was updated and no second run was created
        all_runs = (await session.execute(select(ScrapeRun))).scalars().all()
        assert len(all_runs) == 1
        updated = all_runs[0]
        assert updated.id == run_id
        assert updated.status == "completed"
        assert updated.total_valid_leads == 1
        assert updated.avg_match_score == 85.0
        assert updated.total_raw_jobs == 5


@pytest.mark.asyncio
async def test_jobs_date_filtering_boundary():
    """Ensure date_to (YYYY-MM-DD) includes jobs scraped on that day (end-of-day boundary)."""
    from datetime import datetime
    from backend.crud import get_jobs

    async with TestSessionLocal() as session:
        # Insert a job scraped at 2026-10-25 15:30:00
        job = Job(
            company_name="Date Test Co",
            title="Senior Engineer",
            job_id="date-test-1",
            match_score=90,
            location="Remote",
            scraped_at=datetime(2026, 10, 25, 15, 30, 0)
        )
        session.add(job)
        await session.commit()

        # Query with date_to='2026-10-25' and company='Date Test Co'
        jobs, total = await get_jobs(session, company="Date Test Co", date_from="2026-10-25", date_to="2026-10-25")
        assert total == 1
        assert jobs[0].company_name == "Date Test Co"


@pytest.mark.asyncio
async def test_bulk_delete_and_download_exports():
    """Test bulk deletion and bulk downloading (zip) of exports."""
    import tempfile
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # Login as admin
        r = await client.post("/auth/login", json={"email": "admin@test.com", "password": "password123"})
        token = r.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}

        # Create 2 dummy export records with temporary files
        with tempfile.NamedTemporaryFile(suffix=".xlsx", delete=False) as f1, \
             tempfile.NamedTemporaryFile(suffix=".xlsx", delete=False) as f2:
            f1.write(b"dummy excel 1")
            f2.write(b"dummy excel 2")
            path1, path2 = f1.name, f2.name

        async with TestSessionLocal() as session:
            exp1 = ExportRecord(filename="export_1.xlsx", filepath=path1, row_count=10, avg_match_score=75.0)
            exp2 = ExportRecord(filename="export_2.xlsx", filepath=path2, row_count=20, avg_match_score=85.0)
            session.add_all([exp1, exp2])
            await session.commit()
            await session.refresh(exp1)
            await session.refresh(exp2)
            id1, id2 = exp1.id, exp2.id

        # Test bulk download as ZIP
        res_dl = await client.post("/exports/bulk-download", json={"ids": [id1, id2]}, headers=headers)
        assert res_dl.status_code == 200
        assert "zip" in res_dl.headers.get("content-type", "")

        # Test bulk delete
        res_del = await client.post("/exports/bulk-delete", json={"ids": [id1, id2]}, headers=headers)
        assert res_del.status_code == 200
        assert res_del.json()["affected_count"] == 2

        # Verify soft deleted in DB
        async with TestSessionLocal() as session:
            e1 = await session.get(ExportRecord, id1)
            e2 = await session.get(ExportRecord, id2)
            assert e1.deleted_at is not None
            assert e2.deleted_at is not None


@pytest.mark.asyncio
async def test_bulk_delete_and_download_runs():
    """Test single & bulk deletion and bulk download of scrape runs."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # Login as admin
        r = await client.post("/auth/login", json={"email": "admin@test.com", "password": "password123"})
        token = r.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}

        async with TestSessionLocal() as session:
            r1 = ScrapeRun(status="completed", duration_sec=10.0, total_valid_leads=5, avg_match_score=70.0)
            r2 = ScrapeRun(status="failed", duration_sec=5.0, error_log="Timeout")
            r3 = ScrapeRun(status="running")
            session.add_all([r1, r2, r3])
            await session.commit()
            await session.refresh(r1)
            await session.refresh(r2)
            await session.refresh(r3)
            id1, id2, id3 = r1.id, r2.id, r3.id

        # Test single download
        res_dl_single = await client.get(f"/runs/{id1}/download", headers=headers)
        assert res_dl_single.status_code == 200
        assert "openxmlformats" in res_dl_single.headers.get("content-type", "")

        # Test bulk download
        res_dl_bulk = await client.post("/runs/bulk-download", json={"ids": [id1, id2]}, headers=headers)
        assert res_dl_bulk.status_code == 200
        assert "openxmlformats" in res_dl_bulk.headers.get("content-type", "")

        # Test cannot delete running run directly
        res_del_running = await client.delete(f"/runs/{id3}", headers=headers)
        assert res_del_running.status_code == 409

        # Test bulk delete (r1 and r2 deleted, r3 skipped because active)
        res_del_bulk = await client.post("/runs/bulk-delete", json={"ids": [id1, id2, id3]}, headers=headers)
        assert res_del_bulk.status_code == 200
        assert res_del_bulk.json()["affected_count"] == 2

        # Verify DB state
        async with TestSessionLocal() as session:
            assert await session.get(ScrapeRun, id1) is None
            assert await session.get(ScrapeRun, id2) is None
            assert await session.get(ScrapeRun, id3) is not None
