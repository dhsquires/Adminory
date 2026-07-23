"""Pure tests for Tray estate scoring and triage."""

from datetime import datetime, timedelta, timezone

from app.schemas.tray import (
    EndUserDTO,
    EstateOverview,
    HealthScore,
    KpiSummary,
    SolutionDTO,
    SolutionInstanceDTO,
    TriageSignal,
)
from app.services.tray.health import build_triage, estate_overview, score_instance


def instance(**overrides: object) -> SolutionInstanceDTO:
    values = {
        "id": "instance-1",
        "solution_id": "solution-1",
        "user_id": "user-1",
        "enabled": True,
        "ever_enabled": True,
        "created_at": datetime.now(timezone.utc),
        "source": "official",
    }
    values.update(overrides)
    return SolutionInstanceDTO(**values)


def test_each_health_rule_fires() -> None:
    healthy = score_instance(instance(), KpiSummary(instance_id="instance-1"))
    warning = score_instance(instance(config_complete=False), None)
    critical = score_instance(
        instance(),
        KpiSummary(instance_id="instance-1", error_rate=0.25),
    )
    expired = score_instance(instance(token_expired=True), None)
    broken = score_instance(instance(auth_broken=True), None)
    dead = score_instance(
        instance(
            enabled=False,
            ever_enabled=False,
            created_at=datetime.now(timezone.utc) - timedelta(hours=49),
        ),
        None,
    )

    assert healthy.status == "healthy"
    assert warning.status == "warning"
    assert "misconfig" in warning.reasons
    assert critical.status == "critical"
    assert "error_spike" in critical.reasons
    assert expired.status == "blocked"
    assert "expired_token" in expired.reasons
    assert broken.status == "blocked"
    assert "auth_broken" in broken.reasons
    assert dead.status == "dead_install"


def test_health_severity_precedence_is_blocked_then_critical_then_warning() -> None:
    kpi = KpiSummary(instance_id="instance-1", error_rate=0.5)
    all_three = score_instance(
        instance(token_expired=True, config_complete=False),
        kpi,
    )
    critical_and_warning = score_instance(instance(config_complete=False), kpi)

    assert all_three.status == "blocked"
    assert critical_and_warning.status == "critical"
    assert {"expired_token", "error_spike", "misconfig"} <= set(all_three.reasons)


def test_triage_prioritizes_expired_and_misconfigured_over_dead_install() -> None:
    instances = [
        instance(id="expired", token_expired=True),
        instance(id="misconfigured", config_complete=False),
        instance(
            id="dead",
            enabled=False,
            ever_enabled=False,
            created_at=datetime.now(timezone.utc) - timedelta(hours=72),
        ),
    ]
    signals = build_triage(
        instances,
        [EndUserDTO(external_user_id="external-1", user_id="user-1")],
        [SolutionDTO(id="solution-1")],
        [],
    )

    kinds = [signal.kind for signal in signals]
    assert kinds.index("expired_token") < kinds.index("dead_install")
    assert kinds.index("misconfigured") < kinds.index("dead_install")


def test_estate_overview_rolls_up_totals_and_success_rate() -> None:
    instances = [instance(), instance(id="instance-2", enabled=False)]
    overview = estate_overview(
        instances,
        [EndUserDTO(external_user_id="external-1")],
        [SolutionDTO(id="solution-1")],
        [
            KpiSummary(
                instance_id="instance-1",
                executions=10,
                successful=8,
                failed=2,
                success_rate=0.8,
                error_rate=0.2,
            )
        ],
    )

    assert overview.total_instances == 2
    assert overview.enabled_instances == 1
    assert overview.enabled_ratio == 0.5
    assert overview.success_rate == 0.8


def test_every_dto_carries_source() -> None:
    dto_values = [
        SolutionDTO(id="solution-1"),
        SolutionInstanceDTO(id="instance-1"),
        EndUserDTO(external_user_id="external-1"),
        KpiSummary(),
        HealthScore(status="healthy"),
        TriageSignal(
            kind="dead_install",
            instance_id="instance-1",
            title="Never enabled",
            reason="dead_install",
            severity="dead_install",
        ),
        EstateOverview(),
    ]

    for dto in dto_values:
        assert dto.model_dump()["source"] in {"official", "unofficial"}
