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

        # 3. Debug register config diagnostic
        config_resp = await client.get("/api/debug/register-config")
        assert config_resp.status_code == 200
        config_data = config_resp.json()
        assert config_data["route_exists"] is True
        assert config_data["user_model_loaded"] is True
        assert "registered_routes" in config_data

        # 4. Debug register trace test
        trace_resp = await client.post(
            "/api/debug/register",
            json={
                "email": "debug.test.diagnostic@example.com",
                "password": "DebugPassword123!",
                "full_name": "Diagnostic User",
                "department": "CSE",
                "role": "faculty"
            }
        )
        assert trace_resp.status_code == 200
        trace_data = trace_resp.json()
        assert trace_data["stage"] == "completed"
        assert trace_data["status"] == "success"
        assert trace_data["user_insert_ok"] is True

from app.core.database import engine, Base

@pytest.mark.asyncio
async def test_auth_and_courses_flow():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
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


@pytest.mark.asyncio
async def test_faculty_profile_endpoint_and_cors():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # 1. Unauthenticated request must return 401 Unauthorized (NOT 404)
        resp = await client.get("/api/faculty/profile")
        assert resp.status_code == 401, f"Expected 401 Unauthorized, got {resp.status_code}"
        assert resp.status_code != 404, "Endpoint /api/faculty/profile must not return 404"

        # 2. CORS preflight OPTIONS to /api/faculty/profile
        vercel_origin = "https://qagent-frontend-iota.vercel.app"
        opt_resp = await client.options(
            "/api/faculty/profile",
            headers={
                "Origin": vercel_origin,
                "Access-Control-Request-Method": "GET",
                "Access-Control-Request-Headers": "authorization,content-type",
            }
        )
        assert opt_resp.status_code == 200
        assert opt_resp.headers.get("access-control-allow-origin") == vercel_origin
        assert opt_resp.headers.get("access-control-allow-credentials") == "true"

        # 3. Verify debug/routes endpoint includes /api/faculty/profile
        routes_resp = await client.get("/api/debug/routes")
        assert routes_resp.status_code == 200
        routes_data = routes_resp.json()
        paths = [r["path"] for r in routes_data["routes"]]
        assert "/api/faculty/profile" in paths


@pytest.mark.asyncio
async def test_authenticated_faculty_profile_flows():
    from app.core.database import AsyncSessionLocal
    from app.models.user import User
    from app.models.academic import Course
    from app.core.security import get_password_hash, create_access_token

    uid = uuid.uuid4().hex[:8]
    async with AsyncSessionLocal() as session:
        # Create user with minimal data (testing null safety)
        user = User(
            email=f"prof_{uid}@university.edu",
            full_name=f"Prof. Test {uid}",
            hashed_password=get_password_hash("Pass123!"),
            role="Faculty",
            department=None,  # Null department test
            is_active=True
        )
        session.add(user)
        await session.commit()
        await session.refresh(user)

        # Create course assigned to faculty
        course = Course(
            code=f"CS_{uid}",
            name=f"Distributed Systems {uid}",
            department="Computer Science & Engineering",
            faculty_id=user.id
        )
        session.add(course)
        await session.commit()

        token_int = create_access_token(subject=user.id)
        token_email = create_access_token(subject=user.email)

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # 1. GET with int ID token
        resp1 = await client.get(
            "/api/faculty/profile",
            headers={"Authorization": f"Bearer {token_int}"}
        )
        assert resp1.status_code == 200
        d1 = resp1.json()
        assert d1["email"] == f"prof_{uid}@university.edu"
        assert d1["id"] == user.id
        assert len(d1["assigned_courses"]) >= 1
        assert d1["assigned_courses"][0]["code"] == f"CS_{uid}"
        assert len(d1["courses_assigned"]) >= 1

        # 2. GET with email string token
        resp2 = await client.get(
            "/api/faculty/profile",
            headers={"Authorization": f"Bearer {token_email}"}
        )
        assert resp2.status_code == 200
        d2 = resp2.json()
        assert d2["email"] == f"prof_{uid}@university.edu"

        # 3. PUT update profile
        put_resp = await client.put(
            "/api/faculty/profile",
            headers={"Authorization": f"Bearer {token_int}"},
            json={
                "full_name": "Prof. Updated Name",
                "department": "Information Technology"
            }
        )
        assert put_resp.status_code == 200
        d3 = put_resp.json()
        assert d3["full_name"] == "Prof. Updated Name"
        assert d3["department"] == "Information Technology"

        # 4. Diagnostic endpoint /api/debug/faculty-profile
        diag_resp = await client.get(
            "/api/debug/faculty-profile",
            headers={"Authorization": f"Bearer {token_int}"}
        )
        assert diag_resp.status_code == 200
        diag_data = diag_resp.json()
        assert diag_data["route_exists"] is True
        assert diag_data["authenticated"] is True
        assert diag_data["user_found"] is True
        assert diag_data["database_connected"] is True



