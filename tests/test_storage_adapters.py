import unittest

from bybit_options.storage.adapters.database import SQLAlchemyTradeRepository


class _DummyAsyncSessionMaker:
    def __call__(self):
        raise AssertionError("Session maker should not be called for empty inputs")


class TestStorageAdapters(unittest.IsolatedAsyncioTestCase):
    async def test_sqlalchemy_trade_repository_empty_inputs(self) -> None:
        repo = SQLAlchemyTradeRepository(_DummyAsyncSessionMaker())  # type: ignore[arg-type]

        self.assertEqual(await repo.existing_exec_ids([]), set())
        self.assertEqual(await repo.insert_trades([]), 0)


if __name__ == "__main__":
    unittest.main()
