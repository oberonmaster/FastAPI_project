from fastapi.testclient import TestClient
from main import app


class TestMain:
    """Тесты для main.py"""

    def test_app_creation(self):
        """Тест создания приложения"""
        assert app.title == "FastAPI"

    def test_main_routes_exist(self):
        """Тест что основные роутеры зарегистрированы"""
        client = TestClient(app)


        key_endpoints = [
            "/docs",
            "/auth/register",
            "/api/users/me",
            "/teams/",
        ]

        for endpoint in key_endpoints:
            response = client.get(endpoint) if endpoint != "/auth/register" else client.post(endpoint, json={})
            assert response.status_code != 404, f"Endpoint {endpoint} not found"

    def test_middleware_configured(self):
        """Тест что middleware настроены"""
        middleware_names = [mdw.cls.__name__ for mdw in app.user_middleware]
        assert "SessionMiddleware" in middleware_names


class TestBasicFunctionality:
    """Базовые тесты функциональности"""

    def test_docs_accessible(self):
        """Тест что документация доступна"""
        client = TestClient(app)
        response = client.get("/docs")
        assert response.status_code == 200

    def test_openapi_schema_exists(self):
        """Тест что OpenAPI schema генерируется"""
        client = TestClient(app)
        response = client.get("/openapi.json")
        assert response.status_code == 200