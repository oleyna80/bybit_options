from datetime import datetime, timezone

import pytest

from bybit_options.models import PositionModel, PositionSide, PositionType
from bybit_options.models.greeks import GreeksModel
from bybit_options.models.portfolio import (
    CoinRiskModel,
    MarginModel,
    PortfolioRiskModel,
)
from bybit_options.services.portfolio_syncer import PortfolioSyncer


class _StubRepository:
    def __init__(self) -> None:
        self.snapshots: list[dict] = []

    async def insert_snapshot(self, snapshot):
        self.snapshots.append(dict(snapshot))
        return 1


class _StubOrchestrator:
    def __init__(self, portfolio: PortfolioRiskModel) -> None:
        self.portfolio = portfolio
        self.calls = 0

    async def run_full_analysis(self):
        self.calls += 1
        return self.portfolio


def _build_portfolio() -> PortfolioRiskModel:
    margin = MarginModel(
        account_type="UNIFIED",
        total_equity=1000.0,
        available_balance=800.0,
        used_margin=200.0,
    )

    pos = PositionModel(
        symbol="BTC-30JAN26-100000-C",
        side=PositionSide.BUY,
        size=1.0,
        pos_type=PositionType.OPTION,
        base_coin="BTC",
        greeks=GreeksModel(delta_coin=0.5, gamma_coin=0.01, vega_usd=10.0, theta_usd=-1.0),
    )

    coin_risk = CoinRiskModel(
        base_coin="BTC",
        underlying_price=45000.0,
        positions=[pos],
        total_greeks=GreeksModel(delta_coin=0.5, gamma_coin=0.01, vega_usd=10.0, theta_usd=-1.0),
    )

    return PortfolioRiskModel(
        margin=margin,
        coin_risks={"BTC": coin_risk},
        total_vega_usd=10.0,
        total_theta_usd=-1.0,
        warnings=[],
    )


@pytest.mark.asyncio
async def test_snapshot_row_structure_and_repository_call():
    portfolio = _build_portfolio()
    orchestrator = _StubOrchestrator(portfolio)
    repo = _StubRepository()
    syncer = PortfolioSyncer(orchestrator, repo)

    result = await syncer.take_snapshot()

    assert orchestrator.calls == 1
    assert result.inserted == 1
    assert len(repo.snapshots) == 1

    row = repo.snapshots[0]
    assert {
        "snapshot_time",
        "equity",
        "available_balance",
        "margin_used",
        "total_delta",
        "total_gamma",
        "total_vega",
        "total_theta",
        "btc_price",
        "positions",
    }.issubset(row.keys())
    assert isinstance(row["snapshot_time"], datetime)
    assert row["equity"] == 1000.0
    assert row["available_balance"] == 800.0
    assert row["margin_used"] == 200.0
    assert row["total_delta"] == pytest.approx(0.5)
    assert row["total_gamma"] == pytest.approx(0.01)
    assert row["total_vega"] == pytest.approx(10.0)
    assert row["total_theta"] == pytest.approx(-1.0)
    assert row["btc_price"] == 45000.0


@pytest.mark.asyncio
async def test_positions_serialization_includes_greeks():
    portfolio = _build_portfolio()
    snapshot_time = datetime(2026, 1, 1, tzinfo=timezone.utc)
    row = PortfolioSyncer._build_snapshot_row(portfolio, snapshot_time)

    assert isinstance(row["positions"], list)
    assert row["positions"]
    first = row["positions"][0]
    assert first["symbol"] == "BTC-30JAN26-100000-C"
    assert "greeks" in first
    assert first["greeks"]["delta_coin"] == pytest.approx(0.5)
