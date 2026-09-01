# Skill: Conduct Retrospective (Learning Mode)
     
## Description
Analyzes a completed trade, feature implementation, or bug fix to extract permanent lessons.

## Inputs
- The event description (e.g., "Trade closed with -10% loss" or "Bug #123 fixed").
- The logs/context of what happened.

## Actions
1. **Analyze Root Cause:** Why did this happen? (5 Whys technique).
2. **Extract Rule:** Formulate a generic rule to prevent/repeat this.
   - *Bad:* "Don't buy BTC on Tuesday."
   - *Good:* "Avoid opening Long Call positions 1 hour before CPI Data release."
3. **Update Library:** Append the lesson to `docs/knowledge/ANTI_PATTERNS.md` or `WINNING_PLAYS.md`.
