"""Portfolio snapshot service."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
import json
from typing import Any, Mapping

from bybit_options.models.portfolio import PortfolioRiskModel
from bybit_options.orchestration.analysis_orchestrator import AnalysisOrchestrator
from bybit_options.storage.repositories import PortfolioSnapshotRepository


@dataclass(frozen=True)
class SnapshotResult:
    snapshot_time: datetime
    row: Mapping[str, Any]
    inserted: int


class PortfolioSyncer:
    """Collect and persist portfolio snapshots."""

    def __init__(
        self,
        orchestrator: AnalysisOrchestrator,
        repository: PortfolioSnapshotRepository,
    ) -> None:
        self.orchestrator = orchestrator
        self.repository = repository

    async def take_snapshot(self) -> SnapshotResult:
        portfolio = await self.orchestrator.run_full_analysis()
        snapshot_time = datetime.now(timezone.utc)
        row = self._build_snapshot_row(portfolio, snapshot_time)
        inserted = await self.repository.insert_snapshot(row)
        return SnapshotResult(snapshot_time=snapshot_time, row=row, inserted=inserted)

    @staticmethod
    def _build_snapshot_row(
        portfolio: PortfolioRiskModel, snapshot_time: datetime
    ) -> Mapping[str, Any]:
        margin = portfolio.margin

        total_delta = sum(
            risk.total_greeks.delta_coin for risk in portfolio.coin_risks.values()
        )
        total_gamma = sum(
            risk.total_greeks.gamma_coin for risk in portfolio.coin_risks.values()
        )

        btc_price = None
        if "BTC" in portfolio.coin_risks:
            btc_price = portfolio.coin_risks["BTC"].underlying_price

        positions_payload = [
            pos.model_dump(mode="json")
            for risk in portfolio.coin_risks.values()
            for pos in risk.positions
        ]

        return {
            "snapshot_time": snapshot_time,
            "equity": margin.total_equity,
            "available_balance": margin.available_balance,
            "margin_used": margin.used_margin,
            "total_delta": total_delta,
            "total_gamma": total_gamma,
            "total_vega": portfolio.total_vega_usd,
            "total_theta": portfolio.total_theta_usd,
            "btc_price": btc_price,
            "positions": json.dumps(positions_payload),
        }
