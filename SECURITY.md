# Security Policy

VaaniTrade is an open-source **paper-trading only** research/education project.
It is **not** certified, audited, or approved for live trading with real money
or real brokerage credentials. Do not connect it to a live broker account.

## Reporting a vulnerability

Please open a private security advisory on the repository ("Security" tab →
"Report a vulnerability") instead of filing a public issue. Include:

- A description of the vulnerability and its impact.
- Steps to reproduce.
- Affected version/commit.

We aim to acknowledge reports within 5 business days.

## Security principles used in this codebase

- **No secrets in the frontend.** All AI provider API keys, database
  credentials, and future broker credentials live only in backend
  environment variables (`apps/api/.env`), read via `app/config.py`. They are
  never sent to, embedded in, or logged by the web client.
- **AI output is never trusted.** Every `TradeIntent` produced by an AI
  provider is re-validated against the Pydantic schema on the backend before
  any instrument resolution, risk check, or order action can occur.
- **Deterministic risk and instrument resolution.** Order placement never
  depends solely on an LLM's judgment — the risk engine and instrument
  resolver are plain deterministic code, unit tested independently of any AI
  provider.
- **No autonomous execution.** Orders are placed only after an explicit,
  distinct user confirmation step (`/orders/preview` → `/orders/confirm`)
  tied to an idempotency key.
- **Input sanitization.** Free-text transcripts are length-limited and
  sanitized before being sent to any AI provider or stored.
- **Structured audit logging.** Every parse/validate/confirm/order-response
  cycle is recorded in the audit log. Secrets and API keys are never written
  to logs.
- **CORS and rate limiting.** The API restricts allowed origins via
  `CORS_ORIGINS` and includes a rate-limiting middleware placeholder
  (`app/security.py`) intended to be backed by Redis in production.

## Out of scope / known limitations (MVP)

- No authentication/authorization system is implemented yet (single-tenant
  local/demo use only). Do not expose this deployment to the public internet
  without adding auth.
- Market data is simulated/mocked, not a live feed.
- Real broker adapters are not included; `BrokerAdapter` is a documented
  extension point only.
