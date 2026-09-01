# RFC-001: Option Board & Portfolio Visibility for Strategy Agent
**Status:** ⚠️ DRAFT
**Author:** Solutions Architect
**Date:** 2026-01-22

**Status:** ⚠️ DRAFT (v2)
**Author:** Solutions Architect
**Date:** 2026-01-22

## 1. Context
We need to enable two key consumers to access the **Option Board** in real-time:
1.  **Strategy Agent** (e.g., `DeltaHedgerBot`): Needs data to find hedging instruments and entry points.
2.  **User UI** (Frontend): Needs to display the live board to the human operator.

Currently:
- `LiveStateKeeper` monitors *active positions* only.
- `get_option_board.py` is a standalone script.
- `websocket_manager.py` has a method `broadcast_options_board_update`, but no one calls it systematically.

## 2. Research Findings
- **Existing Code**: `option_board_utils.py` contains robust logic for generating symbols and parsing tickers. `get_option_board.py` demonstrates how to build the board.
- **State Management**: `LiveStateKeeper` is the source of truth for Portfolio data.
- **Gap**: No service exists to "poll" the Option Board on demand for a Strategy.

## 3. Proposed Solution

### A. New Component: `OptionBoardService`
A dedicated service responsible for fetching and caching the option board.

```python
class OptionBoardService:
    def __init__(self, connector: BybitConnector):
        ...
    
    async def get_board(self, base_coin: str, expiry: str) -> OptionBoard:
        """
        Fetches full board (Calls/Puts) for specific expiry.
        Uses asyncio.gather for parallel ticker fetching.
        Returns standardized OptionBoard model.
        """
```

### B. Unified Strategy Context
Instead of passing raw connectors, we inject a `StrategyContext` into the agent.

```python
@dataclass
class StrategyContext:
    portfolio: LiveStateKeeper  # For Account Info, Greeks, Positions
    market: OptionBoardService  # For "Scanning the market"
    execution: OrderExecutor    # For "Acting"
```

### C. Real-Time UI Integration (Pub/Sub)
The `OptionBoardService` will act as a **Publisher**.
When it fetches new data (either via polling or WS), it must:
1.  Return data to the Caller (e.g., Strategy).
2.  **Broadcast** to `WebSocketManager` for the UI.

```python
# In OptionBoardService
async def fetch_and_broadcast(self):
    board = await self.get_board(...)
    
    # Broadcast to UI consumers
    ws_manager = get_websocket_manager()
    await ws_manager.broadcast_options_board_update(board.dict())
    
    return board
```

### D. Data Flow
1.  **Strategy Loop**: Triggers every X seconds.
2.  **Market Scan**:
    - Agent calls `ctx.market.get_board()`.
    - `OptionBoardService` fetches data (API).
    - `OptionBoardService` pushes update to `WebSocketManager`.
    - `WebSocketManager` pushes JSON to Frontend.
3.  **Decision & Execution**: Agent continues logic.

## 4. Risk Assessment
- **Rate Limits**: Fetching the full board (hundreds of tickers) consumes API quota.
    - *Mitigation*: `OptionBoardService` must implement caching (e.g., TTL 5 seconds) and batching.
- **Latency**: Polling 100+ tickers takes 1-2 seconds.
    - *Mitigation*: Acceptable for simple strategies. For HFT, we would need full WS subscription (too expensive for now).

## 5. Recommendation
1.  **Refactor**: Extract `fetch_option_board` logic from `get_option_board.py` into `bybit_options/services/option_board_service.py`.
2.  **Integrate**: Inject this service into the Strategy.
3.  **Reuse**: Strictly use `LiveStateKeeper` for portfolio data (do not duplicate logic).
