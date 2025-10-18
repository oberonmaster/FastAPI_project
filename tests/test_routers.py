from fastapi.testclient import TestClient
from main import app


class TestRouterEndpoints:
    """Тесты существования всех endpoints"""

    def test_auth_endpoints_exist(self):
        """Тест что auth endpoints существуют"""
        client = TestClient(app)

        auth_endpoints = [
            "/auth/jwt/login",
            "/auth/register",
        ]

        for endpoint in auth_endpoints:
            response = client.post(endpoint, json={})
            assert response.status_code != 404

    def test_api_endpoints_exist(self):
        """Тест что API endpoints существуют"""
        client = TestClient(app)

        api_endpoints = [
            "/api/users/me",
            "/teams/",
            "/tasks/",
            "/meetings/",
            "/evaluations/",
            "/calendar/events"
        ]

        for endpoint in api_endpoints:
            response = client.get(endpoint)
            assert response.status_code != 404

    def test_documentation_endpoints(self):
        """Тест что документация доступна"""
        client = TestClient(app)

        for endpoint in ["/docs", "/redoc", "/openapi.json"]:
            response = client.get(endpoint)
            assert response.status_code == 200


class TestRouterValidation:
    """Тесты валидации"""

    def test_invalid_json_returns_422(self):
        """Тест невалидного JSON"""
        client = TestClient(app)
        response = client.post("/teams/", data="invalid json")
        assert response.status_code == 422

    def test_validation_errors_have_detail(self):
        """Тест что ошибки валидации содержат детали"""
        client = TestClient(app)
        response = client.post("/teams/", data="invalid json")
        data = response.json()
        assert "detail" in data


class TestRouterStructure:
    """Тесты структуры роутеров"""

    def test_routers_imported(self):
        """Тест что все роутеры импортированы"""
        from app.routers import users, teams, tasks, meetings, evaluations, calendar
        routers = [users, teams, tasks, meetings, evaluations, calendar]

        for router in routers:
            assert router.router is not None

    def test_route_prefixes_exist(self):
        """Тест что основные префиксы routes существуют"""
        registered_paths = [route.path for route in app.routes]

        required_prefixes = [
            "/auth/",
            "/api/users",
            "/teams",
            "/tasks",
            "/meetings",
            "/evaluations",
            "/calendar"
        ]

        for prefix in required_prefixes:
            assert any(prefix in path for path in registered_paths)