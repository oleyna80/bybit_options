# Anti-Patterns (Lessons Learned)

| Date | Context | Mistake | Lesson Learned (The Rule) |
|------|---------|---------|---------------------------|
| 2026-01-22 | Market Pump | Sold Naked Call (Undefined Risk) | **NEVER sell Naked Calls.** Always use Vertical Spreads (defined risk) or Covered Calls. |
| 2026-01-22 | Live Execution | API Key Missing Trade Scope | **Operational Check:** Always verify API Key permissions (Read-Write vs Read-Only) before deploying live scripts. |
