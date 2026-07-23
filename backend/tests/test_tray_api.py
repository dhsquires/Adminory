"""Hermetic API tests for the internal Tray router."""

from types import SimpleNamespace

from fastapi import FastAPI, HTTPException
from fastapi.testclient import TestClient

from app.api.internal import tray as tray_router
from app.api.tray_deps import require_ops_role
from app.schemas.tray import (
    EndUserDTO,
    EstateOverview,
    HealthScore,
    KpiSummary,
    SolutionDTO,
    SolutionInstanceDTO,
    TriageSignal,
)


def fixture_estate() -> dict[str, object]:
    signal = TriageSignal(
        kind="error_spike",
        instance_id="instance-critical",
        solution_id="solution-1",
        title="Execution error rate is critical",
        reason="error_spike",
        severity="critical",
        executions_at_risk=100,
        blast_radius=101,
        source="unofficial",
    )
    overview = EstateOverview(
        total_solutions=1,
        total_instances=2,
        enabled_instances=1,
        enabled_ratio=0.5,
        total_users=1,
        total_executions=110,
        success_rate=0.8,
        critical_instances=1,
        healthy_instances=1,
        triage=[signal],
        signal_counts={"error_spike": 1},
    )
    return {
        "overview": overview,
        "solutions": [SolutionDTO(id="solution-1", name="Onboarding")],
        "instances": [
            SolutionInstanceDTO(
                id="instance-critical",
                solution_id="solution-1",
                user_id="user-1",
                enabled=True,
                health=HealthScore(
                    instance_id="instance-critical",
                    status="critical",
                    reasons=["error_spike"],
                    source="unofficial",
                ),
            ),
            SolutionInstanceDTO(
                id="instance-healthy",
                solution_id="solution-1",
                user_id="user-1",
                enabled=False,
                health=HealthScore(
                    instance_id="instance-healthy",
                    status="healthy",
                ),
            ),
        ],
        "users": [
            EndUserDTO(external_user_id="external-1", user_id="user-1")
        ],
        "kpis": [
            KpiSummary(
                instance_id="instance-critical",
                executions=100,
                failed=30,
                error_rate=0.3,
            )
        ],
        "timeseries": {"data": [{"time": "2026-07-22", "value": 100}], "source": "unofficial"},
        "triage": [signal],
        "signal_counts": {"error_spike": 1},
    }


def build_app(*, allowed: bool) -> FastAPI:
    app = FastAPI()
    app.include_router(tray_router.router, prefix="/api/internal/tray")

    if allowed:

        async def fake_ops_user() -> SimpleNamespace:
            return SimpleNamespace(role="ops")

        app.dependency_overrides[require_ops_role] = fake_ops_user
    else:

        async def reject_viewer() -> None:
            raise HTTPException(status_code=403, detail="Forbidden")

        app.dependency_overrides[require_ops_role] = reject_viewer

    async def fake_estate() -> dict[str, object]:
        return fixture_estate()

    app.dependency_overrides[tray_router.estate_loader] = fake_estate
    return app


def test_ops_user_can_read_overview_and_filter_instances() -> None:
    with TestClient(build_app(allowed=True)) as client:
        overview = client.get("/api/internal/tray/overview")
        filtered = client.get("/api/internal/tray/instances?state=critical")

    assert overview.status_code == 200
    overview_body = overview.json()
    assert overview_body["total_instances"] == 2
    assert overview_body["triage"][0]["kind"] == "error_spike"
    assert overview_body["signal_counts"] == {"error_spike": 1}
    assert overview_body["source"] == "unofficial"

    assert filtered.status_code == 200
    assert [item["id"] for item in filtered.json()] == ["instance-critical"]
    assert filtered.json()[0]["health"]["source"] == "unofficial"


def test_viewer_gets_403_on_ops_endpoint() -> None:
    with TestClient(build_app(allowed=False)) as client:
        response = client.get("/api/internal/tray/overview")

    assert response.status_code == 403
