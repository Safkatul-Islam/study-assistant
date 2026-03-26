"""Integration tests for the /health endpoint."""


class TestHealth:
    async def test_health_returns_ok(self, root_client):
        resp = await root_client.get("/health")

        assert resp.status_code == 200
        body = resp.json()
        assert body["ok"] is True
        assert body["version"] == "0.1.0"

    async def test_health_method_not_allowed_post(self, root_client):
        resp = await root_client.post("/health")

        assert resp.status_code == 405
