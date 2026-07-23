"""Pydantic contracts for the Tray operations API."""

from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field


Source = Literal["official", "unofficial"]
HealthStatus = Literal["healthy", "warning", "critical", "blocked", "dead_install"]
SignalKind = Literal[
    "expired_token",
    "misconfigured",
    "version_drift",
    "error_spike",
    "dead_install",
    "auth_broken",
]


class TrayDTO(BaseModel):
    """Shared DTO configuration."""

    model_config = ConfigDict(from_attributes=True)


class HealthScore(TrayDTO):
    """Derived operational health for one solution instance."""

    instance_id: str | None = None
    status: HealthStatus
    reasons: list[str] = Field(default_factory=list)
    source: Source = "official"


class SolutionDTO(TrayDTO):
    """A Tray Embedded solution."""

    id: str
    name: str = ""
    state: str | None = None
    version: str | None = None
    latest_version: str | None = None
    active_instances: int = 0
    drift: bool = False
    source: Source = "official"


class SolutionInstanceDTO(TrayDTO):
    """An activated or disabled copy of a solution for one end user."""

    id: str
    name: str = ""
    solution_id: str | None = None
    solution_name: str | None = None
    user_id: str | None = None
    external_user_id: str | None = None
    enabled: bool = False
    ever_enabled: bool = False
    state: str | None = None
    version: str | None = None
    config_complete: bool = True
    missing_required_config: list[str] = Field(default_factory=list)
    auth_healthy: bool = True
    auth_broken: bool = False
    token_expired: bool = False
    token_status: str | None = None
    created_at: datetime | None = None
    workflows: list[dict[str, Any]] = Field(default_factory=list)
    config_slots: list[dict[str, Any]] = Field(default_factory=list)
    auth_slots: list[dict[str, Any]] = Field(default_factory=list)
    recent_executions: list[dict[str, Any]] = Field(default_factory=list)
    health: HealthScore | None = None
    source: Source = "official"


class EndUserDTO(TrayDTO):
    """A Tray Embedded end user and its operational token state."""

    external_user_id: str
    user_id: str | None = None
    name: str | None = None
    token_status: str = "unknown"
    token_expires_at: datetime | None = None
    instance_count: int = 0
    auth_healthy: bool = True
    source: Source = "official"


class KpiSummary(TrayDTO):
    """Execution KPI summary, optionally scoped to one solution instance."""

    instance_id: str | None = None
    executions: int = 0
    successful: int = 0
    failed: int = 0
    success_rate: float = 1.0
    error_rate: float = 0.0
    source: Source = "unofficial"


class TriageSignal(TrayDTO):
    """An actionable estate signal ranked by operational blast radius."""

    kind: SignalKind
    instance_id: str
    solution_id: str | None = None
    user_id: str | None = None
    title: str
    reason: str
    severity: HealthStatus
    users_at_risk: int = 0
    executions_at_risk: int = 0
    blast_radius: int = 0
    source: Source = "official"


class EstateOverview(TrayDTO):
    """Aggregate estate health and its ranked triage queue."""

    total_solutions: int = 0
    total_instances: int = 0
    enabled_instances: int = 0
    enabled_ratio: float = 0.0
    total_users: int = 0
    total_executions: int = 0
    success_rate: float = 1.0
    healthy_instances: int = 0
    warning_instances: int = 0
    critical_instances: int = 0
    blocked_instances: int = 0
    dead_install_instances: int = 0
    triage: list[TriageSignal] = Field(default_factory=list)
    signal_counts: dict[str, int] = Field(default_factory=dict)
    source: Source = "unofficial"


class ConfigValueIn(TrayDTO):
    """One instance config value keyed by a Solution slot external ID."""

    externalId: str
    value: Any


class AuthValueIn(TrayDTO):
    """One instance authentication assignment keyed by external ID."""

    externalId: str
    authId: str


class InstanceConfigUpdate(TrayDTO):
    """Complete config/auth payload for a live Solution instance."""

    config_values: list[ConfigValueIn] = Field(default_factory=list)
    auth_values: list[AuthValueIn] = Field(default_factory=list)
    enable: bool | None = None


class MutationResult(TrayDTO):
    """Safety envelope shared by every mutation endpoint."""

    dry_run: bool
    would_send: dict[str, Any]
    applied: bool
    warning: str | None = None


class ProvisionUserIn(TrayDTO):
    """End-user identity registered with Tray Embedded."""

    name: str
    externalUserId: str


class WizardUrlIn(TrayDTO):
    """Identifiers required to construct a Config Wizard URL."""

    solution_id: str
    instance_id: str


def _slot_value(slot: Any, *names: str, default: Any = None) -> Any:
    if isinstance(slot, dict):
        for name in names:
            if name in slot:
                return slot[name]
        return default
    for name in names:
        if hasattr(slot, name):
            return getattr(slot, name)
    return default


def _slot_groups(
    solution_slots: Any,
) -> tuple[list[Any], list[Any]]:
    if isinstance(solution_slots, dict):
        config_slots = solution_slots.get(
            "config_slots",
            solution_slots.get("configSlots", []),
        )
        auth_slots = solution_slots.get(
            "auth_slots",
            solution_slots.get("authSlots", []),
        )
        return list(config_slots or []), list(auth_slots or [])
    return list(solution_slots or []), []


def validate_config_against_slots(
    update: InstanceConfigUpdate,
    solution_slots: Any,
) -> None:
    """Validate external IDs and required config values before a live write."""
    config_slots, auth_slots = _slot_groups(solution_slots)
    config_ids = {
        str(_slot_value(slot, "externalId", "external_id"))
        for slot in config_slots
        if _slot_value(slot, "externalId", "external_id") is not None
    }
    auth_ids = {
        str(_slot_value(slot, "externalId", "external_id"))
        for slot in auth_slots
        if _slot_value(slot, "externalId", "external_id") is not None
    }

    unknown_config = sorted(
        item.externalId
        for item in update.config_values
        if item.externalId not in config_ids
    )
    unknown_auth = sorted(
        item.externalId
        for item in update.auth_values
        if item.externalId not in auth_ids
    )
    unknown = unknown_config + unknown_auth
    if unknown:
        raise ValueError(
            "Unknown Solution slot externalId(s): " + ", ".join(unknown)
        )

    if update.enable:
        provided = {item.externalId: item.value for item in update.config_values}
        missing: list[str] = []
        for slot in config_slots:
            if not bool(_slot_value(slot, "required", default=False)):
                continue
            external_id = str(_slot_value(slot, "externalId", "external_id", default=""))
            value = provided.get(
                external_id,
                _slot_value(slot, "value", "currentValue", "current_value"),
            )
            if value is None or (isinstance(value, str) and not value.strip()):
                missing.append(external_id)
        if missing:
            raise ValueError(
                "Required config slot(s) must be set before enabling: "
                + ", ".join(sorted(missing))
            )
