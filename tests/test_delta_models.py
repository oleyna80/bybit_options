
import unittest
from decimal import Decimal
from datetime import datetime
from bybit_options.models.delta_models import LargeTradeModel, OrderbookSnapshotModel, DeltaMetricsModel

class TestLargeTradeModel(unittest.TestCase):
    def test_valid_btc_trade(self):
        """Should accept BTC trade >= 5"""
        trade = LargeTradeModel(
            exchange='bybit',
            market_type='spot',
            symbol='BTCUSDT',
            price=Decimal('50000'),
            quantity=Decimal('5.5'),
            side='Buy',
            trade_id='123',
            timestamp=datetime.now()
        )
        self.assertEqual(trade.quantity, Decimal('5.5'))

    def test_invalid_btc_trade(self):
        """Should reject BTC trade < 5"""
        with self.assertRaises(ValueError) as context:
            LargeTradeModel(
                exchange='bybit',
                market_type='spot',
                symbol='BTCUSDT',
                price=Decimal('50000'),
                quantity=Decimal('4.99'),
                side='Buy',
                trade_id='123',
                timestamp=datetime.now()
            )
        self.assertIn('Trade must be >= 5', str(context.exception))

    def test_valid_eth_trade(self):
        """Should accept ETH trade >= 50"""
        trade = LargeTradeModel(
            exchange='deribit',
            market_type='options',
            symbol='ETH-PERP',
            price=Decimal('3000'),
            quantity=Decimal('50'),
            side='Sell',
            trade_id='124',
            timestamp=datetime.now()
        )
        self.assertEqual(trade.quantity, Decimal('50'))

    def test_invalid_eth_trade(self):
        """Should reject ETH trade < 50"""
        with self.assertRaises(ValueError) as context:
            LargeTradeModel(
                exchange='bybit',
                market_type='perpetual',
                symbol='ETHUSDT',
                price=Decimal('3000'),
                quantity=Decimal('49.9'),
                side='Sell',
                trade_id='124',
                timestamp=datetime.now()
            )
        self.assertIn('ETH trade must be >= 50', str(context.exception))

class TestOrderbookSnapshotModel(unittest.TestCase):
    def test_imbalance_calculation(self):
        """Should auto-calculate imbalance"""
        # Bid vol 100, Ask vol 300 -> Total 400 -> Imbalance (100-300)/400 = -0.5
        snapshot = OrderbookSnapshotModel(
            exchange='bybit',
            symbol='BTCUSDT',
            timestamp=datetime.now(),
            bids=[],
            asks=[],
            bid_volume_total=Decimal('100'),
            ask_volume_total=Decimal('300'),
            # imbalance not provided
        )
        self.assertEqual(snapshot.imbalance, Decimal('-0.5'))

    def test_factory_method(self):
        """Should create proper model from raw lists"""
        bids_raw = [[50000, 1.5], [49990, 2.0]]
        asks_raw = [[50010, 1.0], [50020, 0.5]]
        
        snapshot = OrderbookSnapshotModel.from_raw_orderbook(
            exchange='bybit',
            symbol='BTCUSDT',
            bids_raw=bids_raw,
            asks_raw=asks_raw
        )
        
        self.assertEqual(len(snapshot.bids), 2)
        self.assertEqual(snapshot.bids[0].price, Decimal('50000'))
        self.assertEqual(snapshot.bid_volume_total, Decimal('3.5')) # 1.5 + 2.0
        self.assertEqual(snapshot.ask_volume_total, Decimal('1.5')) # 1.0 + 0.5
        
        # Imbalance: (3.5 - 1.5) / 5.0 = 2.0 / 5.0 = 0.4
        self.assertEqual(snapshot.imbalance, Decimal('0.4'))

class TestDeltaMetricsModel(unittest.TestCase):
    def test_delta_calculation(self):
        """Should auto-calculate delta"""
        metrics = DeltaMetricsModel(
            exchange='bybit',
            symbol='BTCUSDT',
            interval='1m',
            timestamp=datetime.now(),
            filtered_buy_volume=Decimal('100'),
            filtered_sell_volume=Decimal('40')
            # filtered_delta not provided
        )
        self.assertEqual(metrics.filtered_delta, Decimal('60'))

if __name__ == '__main__':
    unittest.main()
