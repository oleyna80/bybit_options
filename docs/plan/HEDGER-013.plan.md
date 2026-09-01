# Plan: HEDGER-013 Implement Option Management

## Goal
Implement logic to manage and exit defensive option positions when they are no longer needed (i.e., when the bot switches out of DEFENSIVE mode).

## Rationale
Defensive options are purchased to protect against H4 breakouts. If the price returns to the range (false breakout), the bot switches back to NEUTRAL mode. Keeping the long options incurs unnecessary theta decay. Therefore, we should close these positions when leaving DEFENSIVE mode.

## Scope
1.  **Modify `DeltaHedgerBot`**:
    *   Update `_switch_mode` to detect transition `DEFENSIVE -> ANY`.
    *   Implement `_close_protection_options()` method.
    *   Logic: Fetch all currently held LONG options (assuming this bot manages them) and sell them.
2.  **Update `OrderExecutor`**:
    *   Ensure `place_option_order` supports "Sell" (Close) side correctly (already likely supported, just verification).
3.  **Testing**:
    *   New test case in `test_defensive_mode.py`: `test_exit_defensive_mode_closes_options`.

## Detailed Design

### `_close_protection_options()`
```python
async def _close_protection_options(self):
    # 1. Get current option positions
    positions = await self.connector.get_positions(category="option")
    
    # 2. Filter for Long positions (size > 0)
    long_positions = [p for p in positions if float(p.size) > 0]
    
    for pos in long_positions:
        # 3. Close position (Sell same size)
        # Use Limit order at Bid * 0.95 (marketable limit for closing)
        # or just aggressive limit.
        ...
```

### Risk
*   **Liquidity**: Closing options might be hard if liquidity is gone. We should use a "Marketable Limit" (e.g., Bid * 0.95) or just "Market" if supported and confident. Given the "Buy" used limit, we should stick to Limit.
*   **Portfolio Interference**: If the account has *other* options (not managed by this bot), we might accidentally close them.
    *   *Mitigation*: ideally we track `order_id` from purchase. specific tracking might be too complex for this phase.
    *   *Simplification*: The bot is assumed to be the *sole* manager of this sub-account or at least "Defensive Mode" implies strict control.
    *   *Refinement*: Check if `PositionMonitor` gives us enough info.

## Implementation Steps
1.  Review `BybitConnector.get_positions` return structure.
2.  Implement `_close_protection_options` in `bot.py`.
3.  Add call in `_switch_mode`.
4.  Add unit/integration test.

