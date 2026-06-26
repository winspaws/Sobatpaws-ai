"""Integration tests untuk Sprint 4 endpoints - Admin Panel Integration."""
from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from ekosistem_satwa.api.main import app

client = TestClient(app)


class TestDashboardInsights:
    """Test GET /api/v1/integration/dashboard/insights"""

    def test_health_lists_dashboard(self):
        resp = client.get("/api/v1/integration/health")
        assert resp.status_code == 200
        data = resp.json()
        endpoints = data["data"]["endpoints"]
        assert any("dashboard" in e for e in endpoints)

    def test_returns_species_data(self):
        resp = client.get("/api/v1/integration/dashboard/insights")
        assert resp.status_code == 200
        data = resp.json()["data"]
        assert "species_distribution" in data
        assert "total_species" in data
        assert data["total_species"] >= 10


class TestHealthEndpoint:
    """Test GET /api/v1/integration/health"""

    def test_returns_all_endpoints(self):
        resp = client.get("/api/v1/integration/health")
        assert resp.status_code == 200
        data = resp.json()
        assert data["success"] is True
        endpoints = data["data"]["endpoints"]
        assert len(endpoints) >= 8
        assert any("screening" in e for e in endpoints)
        assert any("medical-history" in e for e in endpoints)
        assert any("dashboard" in e for e in endpoints)
        assert any("health" in e for e in endpoints)
