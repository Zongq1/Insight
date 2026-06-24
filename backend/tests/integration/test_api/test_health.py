"""健康检查 API 测试"""

from fastapi.testclient import TestClient


def test_health_check(client: TestClient) -> None:
    """测试基础健康检查端点"""
    response = client.get("/api/v1/health")
    assert response.status_code == 200

    data = response.json()
    assert data["status"] == "ok"
    assert "timestamp" in data
    assert data["version"] == "0.1.0"


def test_detailed_health_check(client: TestClient) -> None:
    """测试详细健康检查端点"""
    response = client.get("/api/v1/health/detailed")
    assert response.status_code == 200

    data = response.json()
    assert data["status"] in ["ok", "degraded"]
    assert "checks" in data
    assert "database" in data["checks"]
    assert "redis" in data["checks"]
    assert "llm" in data["checks"]
