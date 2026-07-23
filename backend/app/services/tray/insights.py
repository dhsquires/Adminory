"""Unofficial Tray Insights REST operations."""

from datetime import datetime, timedelta, timezone
from typing import Any

from app.services.tray.config import TraySurface


def _period(days: int) -> tuple[str, str]:
    end = datetime.now(timezone.utc)
    start = end - timedelta(days=days)
    return start.isoformat(), end.isoformat()


def _with_source(result: dict[str, Any]) -> dict[str, Any]:
    return {**result, "source": "unofficial"}


class InsightsOperationsMixin:
    """Methods added to TrayClient for the unofficial Insights API."""

    async def _rest(
        self,
        method: str,
        path: str,
        *,
        surface: TraySurface,
        json: dict[str, Any] | None = None,
        params: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        raise NotImplementedError

    async def kpis(self, days: int = 7) -> dict[str, Any]:
        start, end = _period(days)
        result = await self._rest(
            "POST",
            "/insights/v1/executions/kpis",
            surface=TraySurface.INSIGHTS,
            json={"filters": {}, "startPeriod": start, "endPeriod": end},
        )
        return _with_source(result)

    async def timeseries(
        self,
        metric: str = "WORKFLOW_EXECUTIONS",
        days: int = 30,
    ) -> dict[str, Any]:
        start, end = _period(days)
        result = await self._rest(
            "POST",
            "/insights/v1/executions/timeseries",
            surface=TraySurface.INSIGHTS,
            json={
                "filters": {},
                "metric": metric,
                "startPeriod": start,
                "endPeriod": end,
            },
        )
        return _with_source(result)

    async def list_solution_instances(
        self,
        days: int = 7,
        first: int = 200,
    ) -> dict[str, Any]:
        start, end = _period(days)
        result = await self._rest(
            "POST",
            "/insights/v1/list/solutioninstances",
            surface=TraySurface.INSIGHTS,
            json={
                "filters": {},
                "first": first,
                "startPeriod": start,
                "endPeriod": end,
            },
        )
        return _with_source(result)
