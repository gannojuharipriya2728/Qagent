import pytest
import uuid
from httpx import AsyncClient, ASGITransport
from app.main import app

@pytest.mark.asyncio
async def test_health_endpoints():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # 1. Main health
        resp = await client.get("/health")
        assert resp.status_code == 200
        data = resp.json()
        assert "status" in data
        assert "database" in data
        assert "storage" in data
        assert "llm_provider" in data

        # 2. DB health diagnostic
        db_resp = await client.get("/health/db")
        assert db_resp.status_code == 200
        db_data = db_resp.json()
        assert "driver" in db_data
        assert "hostname" in db_data
        assert "database" in db_data
        assert "status" in db_data

from app.core.database import engine, Base

@pytest.mark.asyncio
async def test_auth_and_courses_flow():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        unique_email = f"prof_{uuid.uuid4().hex[:8]}@university.edu"
        password = "SecurePassword123!"

        # 1. Register
        reg_payload = {
            "email": unique_email,
            "password": password,
            "full_name": "Dr. Alan Turing",
            "department": "Computer Science & Engineering",
            "role": "professor"
        }
        reg_resp = await client.post("/api/auth/register", json=reg_payload)
        assert reg_resp.status_code in [200, 201], f"Register failed: {reg_resp.text}"
        reg_data = reg_resp.json()
        assert "access_token" in reg_data

        token = reg_data["access_token"]
        headers = {"Authorization": f"Bearer {token}"}

        # 2. Login
        login_payload = {
            "email": unique_email,
            "password": password
        }
        login_resp = await client.post("/api/auth/login", json=login_payload)
        assert login_resp.status_code == 200
        login_data = login_resp.json()
        assert "access_token" in login_data

        # 3. Fetch courses
        courses_resp = await client.get("/api/courses", headers=headers)
        assert courses_resp.status_code == 200
        courses_data = courses_resp.json()
        assert isinstance(courses_data, list)

@pytest.mark.asyncio
async def test_cors_preflight_and_headers():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # 1. Test OPTIONS preflight from production Vercel frontend
        vercel_origin = "https://qagent-frontend-iota.vercel.app"
        endpoints_to_test = [
            "/api/auth/register",
            "/api/auth/login",
            "/api/courses",
            "/api/resources/upload",
            "/api/generate",
        ]
        
        for ep in endpoints_to_test:
            options_resp = await client.options(
                ep,
                headers={
                    "Origin": vercel_origin,
                    "Access-Control-Request-Method": "POST",
                    "Access-Control-Request-Headers": "content-type,authorization",
                }
            )
            assert options_resp.status_code == 200, f"Preflight failed for {ep}: {options_resp.status_code}"
            assert options_resp.headers.get("access-control-allow-origin") == vercel_origin
            assert options_resp.headers.get("access-control-allow-credentials") == "true"
            assert "POST" in options_resp.headers.get("access-control-allow-methods", "")

        # 2. Test localhost development CORS preflight
        localhost_origins = ["http://localhost:5173", "http://localhost:3000", "http://127.0.0.1:5173"]
        for origin in localhost_origins:
            resp = await client.options(
                "/api/auth/register",
                headers={
                    "Origin": origin,
                    "Access-Control-Request-Method": "POST",
                    "Access-Control-Request-Headers": "content-type",
                }
            )
            assert resp.status_code == 200
            assert resp.headers.get("access-control-allow-origin") == origin

        # 3. Test arbitrary Vercel preview domain regex matching
        preview_origin = "https://qagent-preview-pr-12.vercel.app"
        preview_resp = await client.options(
            "/api/auth/register",
            headers={
                "Origin": preview_origin,
                "Access-Control-Request-Method": "POST",
                "Access-Control-Request-Headers": "content-type",
            }
        )
        assert preview_resp.status_code == 200
        assert preview_resp.headers.get("access-control-allow-origin") == preview_origin

