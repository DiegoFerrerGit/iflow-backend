"""Integration test for the /api/health endpoint.

Requires a running MongoDB instance (see README for Docker instructions).
"""

from httpx import ASGITransport, AsyncClient

from src.main import app


async def test_health_returns_ok():
    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test",
    ) as client:
        response = await client.get("/api/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}
