# PRODUCT Backlog: Bybit Options Platform

**Status:** ACTIVE  
**Version:** v0.3.0-alpha → v1.0.0  
**Created:** 2026-01-17  
**Owner:** Product Manager  
**Target:** Closed Beta Launch

---

## Overview

Product backlog для перехода от MVP к Production-ready Closed Beta.

**Business Model:** Freemium + Bybit Affiliate Commission
- Free: Dashboard, Trading, Strategy Builder (earn on referral %)
- Pro ($29/mo): Analytics + AI Recommendations
- Premium ($99/mo): Full AI Agents + API Access

**Target Users:**
- 🎯 Retail Options Traders (BTC options on Bybit)
- 🏢 Small Prop Desks
- 🔬 Quant Researchers

---

## Technical Decisions

| Decision | Choice | Rationale |
|----------|--------|-----------|
| **Hosting** | Hetzner VPS (Singapore) | Low latency to Bybit, cost-effective |
| **Auth** | Supabase (recommended) | PostgreSQL + Auth, self-hostable |
| **Payments** | LemonSqueezy (Phase 2) | Crypto-friendly, MoR, handles taxes |
| **Launch** | Closed Beta | 5-10 users, iterate on feedback |

---

## Epic 1: Production Infrastructure

**Goal:** Platform runs on production VPS with SSL and backups.

### INFRA-001: Deploy to Hetzner VPS

**Status:** 🔵 TODO

**Priority:** HIGH

**Description:**
Provision Hetzner VPS in Singapore, install Docker, deploy backend + frontend.

**Acceptance Criteria:**
- [ ] AC1: VPS provisioned (Ubuntu 22.04, 4GB RAM minimum)
- [ ] AC2: Docker + Docker Compose installed
- [ ] AC3: Backend API accessible on port 8000
- [ ] AC4: SSH key authentication only

**Estimated effort:** 1 day

---

### INFRA-002: Docker Compose Production

**Status:** 🔵 TODO

**Priority:** HIGH

**Depends on:** INFRA-001

**Description:**
Create production docker-compose.yml with all services.

**Acceptance Criteria:**
- [ ] AC1: docker-compose.prod.yml created
- [ ] AC2: Services: backend, frontend, postgres, (redis optional)
- [ ] AC3: Environment variables from .env file
- [ ] AC4: Restart policies configured

**Estimated effort:** 0.5 day

---

### INFRA-003: SSL Certificate

**Status:** 🔵 TODO

**Priority:** HIGH

**Depends on:** INFRA-001

**Description:**
Configure Let's Encrypt SSL via Certbot or Caddy.

**Acceptance Criteria:**
- [ ] AC1: Domain configured (e.g., app.bybitoptions.com)
- [ ] AC2: HTTPS enabled
- [ ] AC3: Auto-renewal configured
- [ ] AC4: HTTP redirects to HTTPS

**Estimated effort:** 0.5 day

---

### INFRA-004: PostgreSQL Production Setup

**Status:** 🔵 TODO

**Priority:** HIGH

**Description:**
Configure PostgreSQL with secure credentials and proper tuning.

**Acceptance Criteria:**
- [ ] AC1: PostgreSQL in Docker with persistent volume
- [ ] AC2: Strong password, not exposed externally
- [ ] AC3: All migrations applied
- [ ] AC4: Connection pooling (PgBouncer optional)

**Estimated effort:** 0.5 day

---

### INFRA-005: Nginx Reverse Proxy

**Status:** 🔵 TODO

**Priority:** HIGH

**Description:**
Configure Nginx to route traffic to backend and frontend.

**Acceptance Criteria:**
- [ ] AC1: Nginx config for backend (/api → :8000)
- [ ] AC2: Nginx config for frontend (/ → :3002)
- [ ] AC3: WebSocket proxy for /ws
- [ ] AC4: Rate limiting configured

**Estimated effort:** 0.5 day

---

### INFRA-006: Database Backups

**Status:** 🔵 TODO

**Priority:** MEDIUM

**Description:**
Automated daily backups to S3-compatible storage.

**Acceptance Criteria:**
- [ ] AC1: pg_dump cron job (daily)
- [ ] AC2: Upload to Hetzner Object Storage or Backblaze B2
- [ ] AC3: Retention policy (7 days)
- [ ] AC4: Restore tested

**Estimated effort:** 0.5 day

---

## Epic 2: Delta Hedger Production Ready

**Goal:** Hedger bot stable for 24/7 operation with alerts.

### HEDGER-015: Telegram Alerts

**Status:** ✅ DONE

**Priority:** HIGH

**Description:**
Send Telegram notifications on mode changes, orders, errors.

**Acceptance Criteria:**
- [ ] AC1: TelegramAlerter class implemented
- [ ] AC2: Alerts on MODE_SWITCH
- [ ] AC3: Alerts on ORDER_PLACED / ORDER_FAILED
- [ ] AC4: Rate limiting (1 msg/sec max)
- [ ] AC5: Graceful degradation if Telegram unavailable

**Estimated effort:** 2-3 hours

---

### HEDGER-016: Graceful Shutdown

**Status:** 🔵 TODO

**Priority:** MEDIUM

**Description:**
Clean shutdown on SIGTERM: cancel pending orders, save state.

**Acceptance Criteria:**
- [ ] AC1: SIGTERM handler implemented
- [ ] AC2: Pending orders cancelled
- [ ] AC3: State saved to DB
- [ ] AC4: Telegram: "Bot stopped gracefully"
- [ ] AC5: 30 sec timeout, then force exit

**Estimated effort:** 1 hour

---

### HEDGER-017: Kill Switch

**Status:** 🔵 TODO

**Priority:** HIGH

**Description:**
Emergency stop via Telegram command or API endpoint.

**Acceptance Criteria:**
- [ ] AC1: /stop Telegram command
- [ ] AC2: POST /api/hedger/stop endpoint
- [ ] AC3: Immediately stops all trading
- [ ] AC4: Closes all pending orders
- [ ] AC5: Requires confirmation (double-tap)

**Estimated effort:** 1-2 hours

---

### HEDGER-018: Position Limits

**Status:** 🔵 TODO

**Priority:** MEDIUM

**Description:**
Configurable limits on position sizes and order frequency.

**Acceptance Criteria:**
- [ ] AC1: max_delta_exposure config
- [ ] AC2: max_order_per_hour config
- [ ] AC3: max_option_contracts config
- [ ] AC4: Alert when approaching limit

**Estimated effort:** 1 hour

---

### HEDGER-019: 24h Testnet Run

**Status:** 🔵 TODO

**Priority:** HIGH

**Depends on:** HEDGER-015, HEDGER-017

**Description:**
Run hedger on Bybit Testnet for 24 hours, monitor behavior.

**Acceptance Criteria:**
- [ ] AC1: Testnet API keys configured
- [ ] AC2: Run for 24h without crashes
- [ ] AC3: All mode transitions work
- [ ] AC4: Telegram alerts received
- [ ] AC5: Logs reviewed, no errors

**Estimated effort:** 1 day (monitoring)

---

## Epic 3: Authentication (Supabase)

**Goal:** Multi-user authentication with secure API key storage.

### AUTH-001: Supabase Project Setup

**Status:** 🔵 TODO

**Priority:** HIGH

**Description:**
Create Supabase project (cloud or self-hosted).

**Acceptance Criteria:**
- [ ] AC1: Supabase project created
- [ ] AC2: Database connected
- [ ] AC3: Auth enabled (email/password)
- [ ] AC4: API keys stored securely

**Estimated effort:** 1 hour

---

### AUTH-002: Login/Register UI

**Status:** 🔵 TODO

**Priority:** HIGH

**Depends on:** AUTH-001

**Description:**
Frontend login and registration pages.

**Acceptance Criteria:**
- [ ] AC1: Login page (/login)
- [ ] AC2: Register page (/register)
- [ ] AC3: Email verification flow
- [ ] AC4: Password reset flow
- [ ] AC5: Redirect to dashboard after login

**Estimated effort:** 1 day

---

### AUTH-003: API Key Storage Per User

**Status:** 🔵 TODO

**Priority:** HIGH

**Depends on:** AUTH-002

**Description:**
Each user stores their own Bybit API keys (encrypted).

**Acceptance Criteria:**
- [ ] AC1: user_api_keys table created
- [ ] AC2: Keys encrypted at rest (AES-256)
- [ ] AC3: UI to add/remove API keys
- [ ] AC4: Test connection button
- [ ] AC5: Keys never logged

**Estimated effort:** 0.5 day

---

### AUTH-004: Row Level Security

**Status:** 🔵 TODO

**Priority:** HIGH

**Depends on:** AUTH-003

**Description:**
PostgreSQL RLS to isolate user data.

**Acceptance Criteria:**
- [ ] AC1: RLS enabled on all user tables
- [ ] AC2: Users can only see their own data
- [ ] AC3: hedge_actions filtered by user_id
- [ ] AC4: Tested with multiple users

**Estimated effort:** 0.5 day

---

### AUTH-005: Logout + Session Management

**Status:** 🔵 TODO

**Priority:** MEDIUM

**Description:**
Logout functionality, session expiry, token refresh.

**Acceptance Criteria:**
- [ ] AC1: Logout button in UI
- [ ] AC2: Session expires after 7 days
- [ ] AC3: Token refresh works
- [ ] AC4: "Logout all devices" option

**Estimated effort:** 0.5 day

---

## Epic 4: Bybit Affiliate Integration

**Goal:** Earn referral commission on user trades.

### AFFILIATE-001: Get Bybit Affiliate Code

**Status:** 🔵 TODO

**Priority:** HIGH

**Description:**
Apply for Bybit Affiliate program, get referral code.

**Acceptance Criteria:**
- [ ] AC1: Applied to Bybit Affiliate program
- [ ] AC2: Approved and code received
- [ ] AC3: Referral link tested

**Estimated effort:** 1 hour (+ waiting for approval)

---

### AFFILIATE-002: Add Referral to Orders

**Status:** 🔵 TODO

**Priority:** HIGH

**Depends on:** AFFILIATE-001

**Description:**
Include referral code in all order placements via API.

**Acceptance Criteria:**
- [ ] AC1: orderer.place_order includes refCode
- [ ] AC2: Works for futures orders
- [ ] AC3: Works for options orders
- [ ] AC4: Tested in testnet

**Estimated effort:** 2-3 hours

---

### AFFILIATE-003: Track Referral Conversions

**Status:** 🔵 TODO

**Priority:** LOW

**Description:**
Dashboard to view referral earnings (if Bybit API supports).

**Acceptance Criteria:**
- [ ] AC1: Fetch affiliate stats from Bybit
- [ ] AC2: Display in admin dashboard
- [ ] AC3: Track per-user attribution (if possible)

**Estimated effort:** 0.5 day

---

## Epic 5: Onboarding

**Goal:** New users can easily connect and start.

### ONBOARD-001: Welcome Wizard

**Status:** 🔵 TODO

**Priority:** MEDIUM

**Description:**
3-step wizard for new users.

**Acceptance Criteria:**
- [ ] AC1: Step 1: Welcome message + value prop
- [ ] AC2: Step 2: Connect Bybit API
- [ ] AC3: Step 3: View first portfolio analysis
- [ ] AC4: Skip option available
- [ ] AC5: Progress saved

**Estimated effort:** 1 day

---

### ONBOARD-002: API Connection Guide

**Status:** 🔵 TODO

**Priority:** MEDIUM

**Description:**
Step-by-step guide to create Bybit API keys.

**Acceptance Criteria:**
- [ ] AC1: Screenshots of Bybit API page
- [ ] AC2: Required permissions listed
- [ ] AC3: Test connection button
- [ ] AC4: Error messages are helpful

**Estimated effort:** 0.5 day

---

### ONBOARD-003: First Analysis Celebration

**Status:** 🔵 TODO

**Priority:** LOW

**Description:**
Confetti / animation when user sees first portfolio.

**Acceptance Criteria:**
- [ ] AC1: Celebration animation on first load
- [ ] AC2: "Your portfolio is ready!" message
- [ ] AC3: Only shows once

**Estimated effort:** 2 hours

---

## Epic 6: Frontend Polish

**Goal:** UI is stable, usable, and looks professional.

### UI-001: Fix Existing Bugs

**Status:** 🔵 TODO

**Priority:** HIGH

**Description:**
Audit and fix any known frontend bugs.

**Acceptance Criteria:**
- [ ] AC1: Console has no errors
- [ ] AC2: All API calls work
- [ ] AC3: No broken layouts
- [ ] AC4: Loading states implemented

**Estimated effort:** TBD (audit first)

---

### UI-002: Improve Options Board UX

**Status:** 🔵 TODO

**Priority:** MEDIUM

**Description:**
Better filtering, sorting, and display of options chain.

**Acceptance Criteria:**
- [ ] AC1: Filter by expiry
- [ ] AC2: Filter by strike range
- [ ] AC3: Sort by any column
- [ ] AC4: Highlight ITM/OTM
- [ ] AC5: Quick order button

**Estimated effort:** 1-2 days

---

### UI-003: Notifications UI

**Status:** 🔵 TODO

**Priority:** MEDIUM

**Description:**
In-app notifications for alerts and updates.

**Acceptance Criteria:**
- [ ] AC1: Notification bell icon
- [ ] AC2: Dropdown with recent alerts
- [ ] AC3: Unread count badge
- [ ] AC4: Mark as read

**Estimated effort:** 1 day

---

### UI-004: Mobile Responsive

**Status:** 🔵 TODO

**Priority:** LOW

**Description:**
Basic mobile responsiveness for dashboard.

**Acceptance Criteria:**
- [ ] AC1: Dashboard readable on mobile
- [ ] AC2: Navigation works on mobile
- [ ] AC3: Tables scroll horizontally
- [ ] AC4: No horizontal overflow

**Estimated effort:** 1-2 days

---

## Sprint Schedule

### Sprint 1: Infrastructure (Week 1-2)

**Goal:** Platform runs on Hetzner VPS

| Task | Est |
|------|-----|
| INFRA-001 → INFRA-005 | 3 days |
| HEDGER-015 (Telegram) | 3 hours |
| HEDGER-017 (Kill Switch) | 2 hours |
| HEDGER-019 (Testnet Run) | 1 day |

---

### Sprint 2: Auth + Affiliate (Week 3-4)

**Goal:** Multi-user auth works

| Task | Est |
|------|-----|
| AUTH-001 → AUTH-005 | 3 days |
| AFFILIATE-001 → AFFILIATE-002 | 0.5 day |
| UI-001 (Bug fixes) | 2 days |

---

### Sprint 3: Onboarding + Beta (Week 5-6)

**Goal:** Ready for Closed Beta

| Task | Est |
|------|-----|
| ONBOARD-001 → ONBOARD-002 | 1.5 days |
| UI-002 → UI-003 | 2 days |
| Invite beta users | ongoing |
| Collect feedback | ongoing |

---

## Next Steps

```
Start HEDGER-015 (Telegram Alerts)
```

Then proceed to INFRA-001 (Hetzner VPS deployment).
