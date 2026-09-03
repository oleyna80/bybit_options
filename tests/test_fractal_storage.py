import pytest

from strategy.storage.fractal_storage import FractalStorage


class _FakeConnection:
    def __init__(self) -> None:
        self.executed_queries: list[tuple[str, tuple]] = []
        self.fetch_calls: list[tuple[str, tuple]] = []

    async def fetch(self, query: str, *args):
        self.fetch_calls.append((query, args))
        if "INSERT INTO fractals_cache" in query:
            return [{"id": idx + 1} for idx in range(len(args[0]))]
        return []

    async def execute(self, query: str, *args):
        self.executed_queries.append((query, args))
        if "DELETE FROM fractals_cache" in query:
            return "DELETE 1"
        return "DELETE 0"

    def transaction(self):
        return self

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc, tb):
        return False


class _FakePool:
    def __init__(self, connection: _FakeConnection) -> None:
        self.connection = connection

    def acquire(self):
        return self.connection


def _base_fractal():
    return {
        "symbol": "BTCUSDT",
        "timeframe": "H1",
        "fractal_type": "UP",
        "price": 100.0,
        "candle_time": "2026-01-18T00:00:00+00:00",
        "bb_upper_1sigma": 101.0,
        "bb_lower_1sigma": 99.0,
        "bb_upper_2sigma": 102.0,
        "bb_lower_2sigma": 98.0,
        "alligator_teeth": 100.5,
        "is_key_fractal": True,
    }


@pytest.mark.asyncio
async def test_upsert_idempotent_calls_single_insert_batch():
    connection = _FakeConnection()
    storage = FractalStorage(_FakePool(connection))

    fractal = _base_fractal()
    processed = await storage.upsert_fractals([fractal, fractal])

    assert processed == 2
    assert any("INSERT INTO fractals_cache" in call[0] for call in connection.fetch_calls)


@pytest.mark.asyncio
async def test_upsert_updates_fields_on_conflict():
    connection = _FakeConnection()
    storage = FractalStorage(_FakePool(connection))

    fractal = _base_fractal()
    updated = {
        **fractal,
        "is_key_fractal": False,
        "bb_upper_1sigma": 111.0,
        "alligator_teeth": 90.0,
    }

    await storage.upsert_fractals([fractal])
    await storage.upsert_fractals([updated])

    query = connection.fetch_calls[1][0]
    assert "ON CONFLICT" in query
    assert "bb_upper_1sigma = EXCLUDED.bb_upper_1sigma" in query
    assert "alligator_teeth = EXCLUDED.alligator_teeth" in query


@pytest.mark.asyncio
async def test_retention_prune_called_after_upsert():
    connection = _FakeConnection()
    storage = FractalStorage(_FakePool(connection))

    fractal = _base_fractal()
    await storage.upsert_fractals([fractal])

    assert any("DELETE FROM fractals_cache" in call[0] for call in connection.executed_queries)
