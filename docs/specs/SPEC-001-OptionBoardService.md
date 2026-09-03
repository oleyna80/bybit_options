# [SPEC-001] Option Board Service & Real-Time UI Integration
**Status:** ✅ APPROVED
**Author:** Tech Lead
**Date:** 2026-01-22
**Based on:** `docs/research/RFC-001-OptionBoard-Strategy-Link.md`

## 1. 🎯 Objective
Create a reusable `OptionBoardService` that fetches real-time option board data from Bybit. This service must serve two consumers simultaneously:
1.  **Strategy Agents**: Provide data on-demand for trading decisions.
2.  **User UI**: Broadcast the same data via WebSocket for visualization.

## 2. 🏗 Architecture & Data Flow
### Components
1.  **`OptionBoardService`** (`bybit_options/services/option_board_service.py`)
    - Inherits dependencies from `BybitConnector`.
    - Handles fetching tickers in batches (reusing logic from `get_option_board.py`).
    - Implements **Caching** (TTL 1s) to prevent API rate limit abuse.
    - Implements **Pub/Sub** to `WebSocketManager`.

### Dependencies
- `BybitConnector`: For API calls.
- `WebSocketManager`: For broadcasting updates.
- `option_board_utils`: For symbol generation and parsing.

### Flow
1.  Client (Strategy) calls `service.get_board(base_coin, expiry)`.
2.  Service checks Cache.
    - **Hit**: Return cached data.
    - **Miss**:
        1.  Fetch tickers from Bybit API (parallel batching).
        2.  Build `OptionBoard` object (optimized dict).
        3.  Update Cache.
        4.  **Async Broadcast**: Fire-and-forget push to `WebSocketManager`.
3.  `WebSocketManager` broadcasts JSON to connected frontend clients.

## 3. 💾 Data Model / API
### Data Structures (In-Memory)
```python
@dataclass
class OptionBoard:
    timestamp: float
    base_coin: str
    expiry: str
    underlying_price: float
    options: Dict[str, Dict]  # key: symbol, value: Option Data (dict for efficiency)
    
    def to_dict(self):
        # Returns JSON-serializable structure
```

### API Interface
```python
class OptionBoardService:
    def __init__(self, connector: BybitConnector, cache_ttl: float = 1.0):
        ...

    async def get_board(
        self, 
        base_coin: str = "BTC", 
        expiry: str = None
    ) -> OptionBoard:
        """
        Fetches board. 
        If 'expiry' is None, fetches the nearest expiry.
        Side effect: Broadcasts to WebSocket.
        """
```

## 4. ladder Implementation Plan
1.  [ ] **Create Service Class**
    - File: `bybit_options/services/option_board_service.py`
    - Port logic from `get_option_board.py` (fetching, batching, formatting).
2.  [ ] **Implement Caching & Broadcasting**
    - Add `_cache` dict and timestamp check.
    - Add `WebSocketManager` integration.
3.  [ ] **Refactor `get_option_board.py`**
    - Make the script use the new service instead of raw logic.
    - This proves the service works.
4.  [ ] **Tests**
    - Create `tests/test_option_board_service.py` (Mocking connector).

## 5. 🧪 Verification
- **Manual**: Run `python get_option_board.py`. It should work exactly as before.
- **WebSocket**: Connect a WS client (or use UI), trigger the script, verify message reception.

## 6. 🛡 Risks & Edge Cases
- **Rate Limits**: If Cache fails, we might hit Bybit limits.
- **WS Overhead**: Serialization of large boards (100+ items) might be slow. *Mitigation: Broadcast asynchronously.*
