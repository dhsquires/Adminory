"""Pure health scoring and triage functions for a Tray estate."""

from collections import Counter
from datetime import datetime, timedelta, timezone
from typing import Iterable

from app.schemas.tray import (
    EndUserDTO,
    EstateOverview,
    HealthScore,
    KpiSummary,
    SolutionDTO,
    SolutionInstanceDTO,
    TriageSignal,
)


ERROR_RATE_CRITICAL = 0.25
DEAD_INSTALL_HOURS = 48

_STATUS_PRIORITY = {
    "healthy": 0,
    "dead_install": 1,
    "warning": 2,
    "critical": 3,
    "blocked": 4,
}
_SIGNAL_PRIORITY = {
    "expired_token": 6,
    "auth_broken": 5,
    "error_spike": 4,
    "misconfigured": 3,
    "version_drift": 2,
    "dead_install": 1,
}


def _is_dead_install(
    instance: SolutionInstanceDTO,
    *,
    now: datetime | None = None,
) -> bool:
    if instance.enabled or instance.ever_enabled or instance.created_at is None:
        return False
    created_at = instance.created_at
    if created_at.tzinfo is None:
        created_at = created_at.replace(tzinfo=timezone.utc)
    reference = now or datetime.now(timezone.utc)
    return reference - created_at > timedelta(hours=DEAD_INSTALL_HOURS)


def _token_expired(instance: SolutionInstanceDTO) -> bool:
    return instance.token_expired or (instance.token_status or "").lower() == "expired"


def _missing_config(instance: SolutionInstanceDTO) -> bool:
    return not instance.config_complete or bool(instance.missing_required_config)


def score_instance(
    instance: SolutionInstanceDTO,
    kpi: KpiSummary | None,
) -> HealthScore:
    """Score one instance, selecting the highest applicable severity."""
    findings: list[tuple[str, str]] = []

    if _token_expired(instance):
        findings.append(("blocked", "expired_token"))
    if instance.auth_broken or not instance.auth_healthy:
        findings.append(("blocked", "auth_broken"))
    if kpi is not None and kpi.error_rate >= ERROR_RATE_CRITICAL:
        findings.append(("critical", "error_spike"))
    if instance.enabled and _missing_config(instance):
        findings.append(("warning", "misconfig"))
    if _is_dead_install(instance):
        findings.append(("dead_install", "dead_install"))

    if not findings:
        return HealthScore(
            instance_id=instance.id,
            status="healthy",
            reasons=[],
            source="unofficial" if kpi is not None else "official",
        )

    status = max(findings, key=lambda finding: _STATUS_PRIORITY[finding[0]])[0]
    return HealthScore(
        instance_id=instance.id,
        status=status,
        reasons=[reason for _, reason in findings],
        source="unofficial" if kpi is not None else "official",
    )


def _kpi_map(kpis: Iterable[KpiSummary]) -> dict[str, KpiSummary]:
    return {kpi.instance_id: kpi for kpi in kpis if kpi.instance_id is not None}


def _solution_map(solutions: Iterable[SolutionDTO]) -> dict[str, SolutionDTO]:
    return {solution.id: solution for solution in solutions}


def _users_for_instance(
    instance: SolutionInstanceDTO,
    users: Iterable[EndUserDTO],
) -> int:
    identifiers = {instance.user_id, instance.external_user_id} - {None}
    if not identifiers:
        return 0
    return int(
        any(
            user.user_id in identifiers or user.external_user_id in identifiers
            for user in users
        )
    )


def _signal(
    kind: str,
    instance: SolutionInstanceDTO,
    kpi: KpiSummary | None,
    users_at_risk: int,
) -> TriageSignal:
    details = {
        "expired_token": ("Tray user token expired", "blocked"),
        "auth_broken": ("Authentication is broken", "blocked"),
        "error_spike": ("Execution error rate is critical", "critical"),
        "misconfigured": ("Required configuration is missing", "warning"),
        "version_drift": ("Instance is behind the solution version", "warning"),
        "dead_install": ("Instance was never enabled", "dead_install"),
    }
    title, severity = details[kind]
    executions = kpi.executions if kpi is not None else 0
    return TriageSignal(
        kind=kind,  # type: ignore[arg-type]
        instance_id=instance.id,
        solution_id=instance.solution_id,
        user_id=instance.user_id or instance.external_user_id,
        title=title,
        reason=kind,
        severity=severity,  # type: ignore[arg-type]
        users_at_risk=users_at_risk,
        executions_at_risk=executions,
        blast_radius=users_at_risk + executions,
        source="unofficial" if kind == "error_spike" else "official",
    )


def build_triage(
    instances: list[SolutionInstanceDTO],
    users: list[EndUserDTO],
    solutions: list[SolutionDTO],
    kpis: list[KpiSummary],
) -> list[TriageSignal]:
    """Build a blast-radius-ranked queue of actionable instance signals."""
    kpi_by_instance = _kpi_map(kpis)
    solution_by_id = _solution_map(solutions)
    signals: list[TriageSignal] = []

    for instance in instances:
        kpi = kpi_by_instance.get(instance.id)
        users_at_risk = _users_for_instance(instance, users)
        kinds: list[str] = []

        if _token_expired(instance):
            kinds.append("expired_token")
        if instance.auth_broken or not instance.auth_healthy:
            kinds.append("auth_broken")
        if kpi is not None and kpi.error_rate >= ERROR_RATE_CRITICAL:
            kinds.append("error_spike")
        if instance.enabled and _missing_config(instance):
            kinds.append("misconfigured")

        solution = solution_by_id.get(instance.solution_id or "")
        if solution is not None and (
            solution.drift
            or (
                instance.version is not None
                and solution.version is not None
                and instance.version != solution.version
            )
        ):
            kinds.append("version_drift")
        if _is_dead_install(instance):
            kinds.append("dead_install")

        signals.extend(
            _signal(kind, instance, kpi, users_at_risk) for kind in kinds
        )

    return sorted(
        signals,
        key=lambda signal: (
            -signal.blast_radius,
            -_SIGNAL_PRIORITY[signal.kind],
            signal.instance_id,
        ),
    )


def estate_overview(
    instances: list[SolutionInstanceDTO],
    users: list[EndUserDTO],
    solutions: list[SolutionDTO],
    kpis: list[KpiSummary],
) -> EstateOverview:
    """Roll up estate totals, health distribution, and triage signals."""
    kpi_by_instance = _kpi_map(kpis)
    scores = [
        instance.health or score_instance(instance, kpi_by_instance.get(instance.id))
        for instance in instances
    ]
    statuses = Counter(score.status for score in scores)
    triage = build_triage(instances, users, solutions, kpis)
    signal_counts = dict(Counter(signal.kind for signal in triage))
    executions = sum(kpi.executions for kpi in kpis)
    successful = sum(kpi.successful for kpi in kpis)
    enabled = sum(instance.enabled for instance in instances)

    return EstateOverview(
        total_solutions=len(solutions),
        total_instances=len(instances),
        enabled_instances=enabled,
        enabled_ratio=enabled / len(instances) if instances else 0.0,
        total_users=len(users),
        total_executions=executions,
        success_rate=successful / executions if executions else 1.0,
        healthy_instances=statuses["healthy"],
        warning_instances=statuses["warning"],
        critical_instances=statuses["critical"],
        blocked_instances=statuses["blocked"],
        dead_install_instances=statuses["dead_install"],
        triage=triage,
        signal_counts=signal_counts,
        source="unofficial",
    )
