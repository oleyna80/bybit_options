"""
Analysis Orchestrator - Coordinates the entire risk analysis workflow
This is the "Controller" that ties together all services
"""
import asyncio
from typing import List, Dict, Set, Optional
import logging

from bybit_options.services.bybit_connector import BybitConnector
from bybit_options.services.market_data_service import MarketDataService
from bybit_options.core.risk_engine import RiskEngine
from bybit_options.models import (
    PositionModel, PositionType, PortfolioRiskModel
)

logger = logging.getLogger(__name__)


class AnalysisOrchestrator:
    """
    High-level orchestrator for risk analysis
    Coordinates data fetching, calculation, and enrichment
    """
    
    def __init__(self, connector: BybitConnector):
        self.connector = connector
        self.market_data = MarketDataService(connector)
        self.risk_engine = RiskEngine()
    
    async def run_full_analysis(
        self,
        fetch_enhanced_metrics: bool = True
    ) -> PortfolioRiskModel:
        """
        Execute complete risk analysis pipeline
        
        Steps:
        1. Fetch all positions
        2. Fetch margin info
        3. Identify required market data
        4. Fetch market data in parallel
        5. Calculate Greeks and risk metrics
        6. Enrich with enhanced metrics (IV, slippage, gamma rent)
        7. Aggregate and build portfolio model
        
        Args:
            fetch_enhanced_metrics: Include IV, slippage, gamma rent
        
        Returns:
            Complete portfolio risk model
        """
        logger.info("Starting full risk analysis...")
        
        # Step 1: Fetch positions
        raw_positions = await self.market_data.fetch_all_positions()
        
        if not raw_positions:
            logger.warning("No positions found")
            return PortfolioRiskModel(
                margin=await self.market_data.fetch_margin_info()
            )
        
        logger.info(f"Processing {len(raw_positions)} positions")
        
        # Step 2: Fetch margin info
        margin = await self.market_data.fetch_margin_info()
        
        # Step 3: Identify required data
        option_positions = [
            p for p in raw_positions
            if p.get("_category") == "option"
        ]
        
        base_coins: Set[str] = {
            self.risk_engine.extract_base_coin(p["symbol"])
            for p in raw_positions
        }
        
        option_coins: Set[str] = {
            self.risk_engine.extract_base_coin(p["symbol"])
            for p in option_positions
        }
        
        logger.info(f"Base coins: {base_coins}")
        logger.info(f"Option coins: {option_coins}")
        
        # Step 4: Fetch market data in parallel
        greeks_task = self.market_data.fetch_option_greeks(option_coins)
        prices_task = self.market_data.fetch_underlying_prices(base_coins)
        
        _, underlying_prices = await asyncio.gather(greeks_task, prices_task)
        
        # Step 5: Calculate Greeks for all positions
        positions = await self._process_positions(
            raw_positions,
            underlying_prices
        )
        
        # Step 6: Enrich with enhanced metrics
        if fetch_enhanced_metrics:
            await self._enrich_positions(positions, underlying_prices)
        
        # Step 7: Build portfolio model
        portfolio = self.risk_engine.build_portfolio_risk(
            positions=positions,
            margin=margin,
            underlying_prices=underlying_prices
        )
        
        logger.info("Analysis complete")
        
        return portfolio
    
    async def _process_positions(
        self,
        raw_positions: List[Dict],
        underlying_prices: Dict[str, float]
    ) -> List[PositionModel]:
        """
        Process raw positions into PositionModel objects with Greeks
        """
        positions = []
        
        for raw_pos in raw_positions:
            symbol = raw_pos.get("symbol", "")
            category = raw_pos.get("_category", "")
            
            # Determine position type
            pos_type = (
                PositionType.OPTION if category == "option"
                else PositionType.LINEAR if category == "linear"
                else PositionType.LINEAR
            )
            
            # Extract base coin
            base_coin = self.risk_engine.extract_base_coin(symbol)
            
            # For options: extract details
            series, option_type, strike = None, None, None
            if pos_type == PositionType.OPTION:
                series, option_type, strike = \
                    self.risk_engine.extract_option_details(symbol)
            
            # Get ticker data
            ticker_data = None
            if pos_type == PositionType.OPTION:
                ticker_data = self.market_data.get_ticker(symbol)
            
            # Calculate Greeks
            greeks = self.risk_engine.calculate_position_greeks(
                raw_position=raw_pos,
                ticker_data=ticker_data,
                pos_type=pos_type
            )
            
            # Build position model
            position = self.risk_engine.build_position_model(
                raw_position=raw_pos,
                greeks=greeks,
                pos_type=pos_type,
                base_coin=base_coin,
                series=series,
                option_type=option_type,
                strike=strike
            )
            
            positions.append(position)
        
        return positions
    
    async def _enrich_positions(
        self,
        positions: List[PositionModel],
        underlying_prices: Dict[str, float]
    ):
        """
        Enrich positions with advanced metrics:
        - IV comparison vs ATM
        - Slippage metrics
        - Gamma Rent
        """
        for pos in positions:
            # Only for options
            if pos.pos_type != PositionType.OPTION:
                continue
            
            ticker = self.market_data.get_ticker(pos.symbol)
            if not ticker:
                continue
            
            # 1. IV Metrics
            if pos.series and pos.base_coin in underlying_prices:
                position_iv = float(ticker.get("markIv", 0)) or None
                
                if position_iv:
                    atm_iv = await self.market_data.fetch_atm_iv(
                        base_coin=pos.base_coin,
                        series=pos.series,
                        underlying_price=underlying_prices[pos.base_coin]
                    )
                    
                    pos.iv_metrics = self.risk_engine.calculate_iv_metrics(
                        position_iv=position_iv,
                        atm_iv=atm_iv
                    )
            
            # 2. Slippage Metrics
            mark_price = float(ticker.get("markPrice", 0))
            if mark_price > 0:
                pos.slippage = self.market_data.calculate_slippage(
                    symbol=pos.symbol,
                    mark_price=mark_price
                )
            
            # 3. Gamma Rent
            if abs(pos.greeks.gamma_coin) > 1e-10:
                pos.gamma_rent = self.risk_engine.calculate_gamma_rent(
                    theta_usd=pos.greeks.theta_usd,
                    gamma_coin=pos.greeks.gamma_coin
                )
