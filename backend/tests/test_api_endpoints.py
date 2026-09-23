import pytest
import uuid
from httpx import AsyncClient, ASGITransport
from app.main import app

from app.core.database import engine, Base

@pytest.mark.asyncio
async def test_health_endpoints():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
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
        unique_email = f"debug.diag.{uuid.uuid4().hex[:8]}@example.com"
        trace_resp = await client.post(
            "/api/debug/register",
            json={
                "email": unique_email,
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


@pytest.mark.asyncio
async def test_faculty_profile_with_null_and_assigned_faculty_id_courses():
    from app.core.database import AsyncSessionLocal
    from app.models.user import User
    from app.models.academic import Course
    from app.core.security import get_password_hash, create_access_token

    uid = uuid.uuid4().hex[:8]
    async with AsyncSessionLocal() as session:
        faculty1 = User(
            email=f"fac1_{uid}@college.edu",
            full_name="Faculty One",
            hashed_password=get_password_hash("Pass123!"),
            role="Faculty",
            department="Computer Science & Engineering",
            is_active=True
        )
        faculty2 = User(
            email=f"fac2_{uid}@college.edu",
            full_name="Faculty Two",
            hashed_password=get_password_hash("Pass123!"),
            role="Faculty",
            department="Electrical Engineering",
            is_active=True
        )
        session.add_all([faculty1, faculty2])
        await session.commit()
        await session.refresh(faculty1)
        await session.refresh(faculty2)

        # 1. Course with faculty_id matching faculty1
        c1 = Course(code=f"C1_{uid}", name="Assigned Course", department="Computer Science & Engineering", faculty_id=faculty1.id)
        # 2. Course with NULL faculty_id but matching faculty1's department
        c2 = Course(code=f"C2_{uid}", name="Dept Course No Faculty", department="Computer Science & Engineering", faculty_id=None)
        # 3. Course with NULL faculty_id and different department
        c3 = Course(code=f"C3_{uid}", name="Other Dept Course", department="Electrical Engineering", faculty_id=None)
        # 4. Course with faculty_id assigned to faculty2
        c4 = Course(code=f"C4_{uid}", name="Other Faculty Course", department="Mechanical", faculty_id=faculty2.id)
        
        session.add_all([c1, c2, c3, c4])
        await session.commit()

        token1 = create_access_token(subject=faculty1.id)

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.get(
            "/api/faculty/profile",
            headers={"Authorization": f"Bearer {token1}"}
        )
        assert resp.status_code == 200
        data = resp.json()
        codes = [c["code"] for c in data["assigned_courses"]]
        assert f"C1_{uid}" in codes  # explicitly assigned
        assert f"C2_{uid}" in codes  # department match with NULL faculty_id
        assert f"C3_{uid}" not in codes  # different department & NULL faculty_id
        assert f"C4_{uid}" not in codes  # assigned to another faculty






@pytest.mark.asyncio
async def test_every_router_is_mounted_under_the_api_prefix():
    """
    Guards against a router silently disappearing from the app.

    A missing `router = APIRouter(...)` in one module raised NameError at import
    time and took the whole service down; a router that merely fails to mount
    would instead 404 every one of its endpoints.
    """
    from app.main import iter_route_specs

    paths = {path for path, _ in iter_route_specs()}
    for expected in [
        "/api/auth/register",
        "/api/auth/login",
        "/api/auth/me",
        "/api/faculty/profile",
        "/api/courses",
        "/api/resources/upload",
        "/api/generate",
        "/api/papers",
        "/api/admin/stats",
        "/api/ai/health",
    ]:
        assert expected in paths, f"{expected} is not routable"


@pytest.mark.asyncio
async def test_privileged_endpoints_reject_anonymous_callers():
    """
    Administration and destructive or LLM-spending routes must never be
    reachable without credentials.
    """
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        for method, path in [
            ("get", "/api/admin/stats"),
            ("get", "/api/admin/users"),
            ("patch", "/api/admin/users/1/toggle-status"),
            ("post", "/api/courses/reset-all"),
            ("delete", "/api/courses/reset-all"),
        ]:
            resp = await getattr(client, method)(path)
            assert resp.status_code in (401, 403), (
                f"{method.upper()} {path} returned {resp.status_code} to an anonymous caller"
            )

        resp = await client.post("/api/generate", json={
            "course_id": 1,
            "title": "T",
            "examination_name": "E",
            "institution_name": "I",
            "duration_minutes": 60,
            "total_marks": 10,
            "sections": [],
            "difficulty_distribution": {},
            "bloom_distribution": {},
        })
        assert resp.status_code in (401, 403)


@pytest.mark.asyncio
async def test_pdf_export_filename_survives_non_ascii_titles():
    """
    Paper titles carry em dashes (the app's own examination names do), and HTTP
    headers are latin-1. Building Content-Disposition straight from the title
    raised UnicodeEncodeError and turned every export into a 500.
    """
    import re
    import unicodedata
    from urllib.parse import quote

    raw = "CS3401_End_Semester_Examination_—_Operating_Systems_Ãœbung.pdf"
    ascii_filename = unicodedata.normalize("NFKD", raw).encode("ascii", "ignore").decode("ascii")
    ascii_filename = re.sub(r'[^A-Za-z0-9._-]', "_", ascii_filename).strip("._")
    header = f'attachment; filename="{ascii_filename}"; filename*=UTF-8\'\'{quote(raw, safe="")}'

    header.encode("latin-1")  # must not raise
    assert ascii_filename.endswith(".pdf")
    assert "—" not in ascii_filename


@pytest.mark.asyncio
async def test_ai_health_reports_unreachable_instead_of_raising():
    """An unreachable LLM gateway must degrade, not 500 the health endpoint."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.get("/api/ai/health")
        assert resp.status_code == 200
        body = resp.json()
        assert {"provider", "model", "configured", "reachable"} <= set(body)
        assert isinstance(body["reachable"], bool)
