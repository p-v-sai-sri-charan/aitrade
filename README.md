# VaaniTrade

VaaniTrade is an open-source, mobile-first, voice-enabled assistant for **paper
trading** Indian (NSE) stocks in Hindi, Hinglish, and English.

> ⚠️ **Paper trading only.** VaaniTrade simulates orders against mocked
> market data and a simulated broker. It is not connected to any real
> brokerage, exchange, or bank account, and it is not certified or approved
> for live trading. See [`SECURITY.md`](./SECURITY.md).

```
"Reliance ke 10 shares 2950 limit price par buy karo."
```
&rarr; VaaniTrade transcribes it, extracts a structured order, resolves the
exact NSE instrument, runs deterministic risk checks, shows you a summary,
speaks it back, and only places the (paper) order after you explicitly
confirm.

## Why it's built this way

- **AI extracts, it never executes.** A provider-neutral `AIProvider`
  interface (`packages/ai-providers`) turns speech/text into a structured
  `TradeIntent`. The backend independently re-validates that JSON against
  its own Pydantic schema, resolves the instrument deterministically
  (never guessing an ambiguous company name), and runs a pure, dependency-free
  risk engine (`packages/risk-engine`) before anything can be previewed --
  let alone confirmed.
- **No order without explicit confirmation.** `/orders/preview` and
  `/orders/confirm` are separate calls tied together by a short-lived
  preview and an idempotency key, so a spoken "Confirm buy" can never
  double-submit or apply to stale numbers.
- **Runs with zero API keys.** The default AI provider (`mock`) is a
  deterministic rule-based parser -- no LLM required to develop, test, or
  demo the whole flow end to end.
- **Ready for a native app later.** Microphone/speech (`packages/voice`) and
  local storage (`apps/web/src/services/storage`) sit behind small
  interfaces so a Capacitor or React Native build can swap in native
  implementations without touching business logic.

## Monorepo layout

```
vaanitrade/
├── apps/
│   ├── web/            Vite + React + TypeScript PWA (mobile-first UI)
│   └── api/             FastAPI backend
├── packages/
│   ├── shared-types/     TypeScript types shared by the web app (and a future RN app)
│   ├── voice/            VoiceService interface + Web Speech API browser implementation
│   ├── ai-providers/     Provider-neutral AIProvider interface + adapters (Python)
│   ├── risk-engine/       Deterministic, dependency-free risk rules (Python)
│   └── broker-core/       BrokerAdapter interface + simulated PaperBroker (Python)
├── docker-compose.yml
├── .env.example
```

## Quick start (Docker)

```bash
cp .env.example .env
docker compose up --build
```

- Web app: http://localhost:5173
- API: http://localhost:8000 (docs at http://localhost:8000/docs)
- The database is seeded automatically with demo positions/orders/audit log
  entries on first startup so the UI isn't empty.

The default `AI_PROVIDER=mock` needs no API key. To use a real LLM, set
`AI_PROVIDER` and the matching `*_API_KEY` in `.env` (see below) and re-run
`docker compose up --build`.

## Running without Docker

### Backend (FastAPI)

Requires Python 3.11+ and a running Postgres (or point `DATABASE_URL` at a
local SQLite file for quick local hacking, e.g.
`sqlite:///./vaanitrade.db`).

```bash
cd apps/api
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt   # also installs packages/{risk-engine,ai-providers,broker-core} editable
cp ../../.env.example .env        # edit DATABASE_URL etc. as needed
uvicorn app.main:app --reload --port 8000
```

### Frontend (Vite + React)

Requires Node.js 20+.

```bash
npm install                        # from the repo root -- installs all npm workspaces
npm run dev:web                    # or: cd apps/web && npm run dev
```

Set `apps/web/.env` (or repo-root `.env`, read by Vite) with:

```
VITE_API_BASE_URL=http://localhost:8000/api/v1
VITE_WS_BASE_URL=ws://localhost:8000/ws
```

## Sample commands to try

| Language | Command |
| --- | --- |
| Hinglish | `Reliance ke 10 shares 2950 limit price par buy karo.` |
| English | `Buy 5 shares of Infosys at market price` |
| Hindi (Devanagari) | `टीसीएस के 3 शेयर मार्केट प्राइस पर खरीदो` |
| Ambiguous (by design) | `Tata ka share buy karo.` &rarr; asks you to pick the exact Tata company |
| Portfolio | `mera portfolio dikhao` / `show my portfolio` |
| Orders | `show my orders` |
| Cancel | `order cancel karo` |
| Confirmation | `Confirm`, `Confirm buy`, `haan confirm karo`, `order confirm karo` |

The `mock` AI provider (default) handles all of the above without any API
key; a real LLM provider will generally understand a wider range of
phrasing.

## Configuration (`.env`)

See [`.env.example`](./.env.example) for the full list. Key variables:

| Variable | Purpose |
| --- | --- |
| `AI_PROVIDER` | `mock` \| `anthropic` \| `openai` \| `gemini` \| `local` \| `ollama` |
| `ANTHROPIC_API_KEY` / `OPENAI_API_KEY` / `GEMINI_API_KEY` | Only needed for the matching provider. **Backend-only, never sent to the frontend.** |
| `LOCAL_AI_BASE_URL` / `OLLAMA_BASE_URL` | Point at a self-hosted OpenAI-compatible server or Ollama instance |
| `MARKET_DATA_PROVIDER` | `mock` (seeded/offline, default) \| `yahoo` (live-ish prices for any NSE symbol, no API key -- see [Market data & instrument universe](#market-data--instrument-universe)) |
| `INSTRUMENT_SOURCE` | `seeded` (curated ~20-stock list, default) \| `nse` (auto-fetches the full NSE-listed equity universe) |
| `DATABASE_URL` | SQLAlchemy connection string (Postgres in Docker; SQLite works for local hacking) |
| `RISK_MAX_ORDER_VALUE`, `RISK_MAX_QUANTITY`, `RISK_MAX_PRICE_DEVIATION_PCT`, `RISK_DAILY_LOSS_LIMIT` | Default risk limits (also editable per-session in Settings) |
| `TRADING_KILL_SWITCH` | Set `true` to block all order placement |
| `PAPER_STARTING_BALANCE`, `PAPER_SLIPPAGE_BPS`, `PAPER_BROKERAGE_FLAT`, `PAPER_STT_RATE_SELL`, `PAPER_GST_RATE` | Paper broker simulation parameters |
| `VITE_API_BASE_URL`, `VITE_WS_BASE_URL` | Frontend-only, no secrets |

## Market data & instrument universe

By default VaaniTrade runs fully offline: a seeded list of ~20 NSE stocks
(`INSTRUMENT_SOURCE=seeded`) with jittered mock prices
(`MARKET_DATA_PROVIDER=mock`). Two opt-in sources auto-fetch the real thing
instead, each behind the same interface so nothing else in the app changes:

- **`INSTRUMENT_SOURCE=nse`** -- fetches NSE's public equity list CSV
  (`broker_core/instrument_repository_live.py`) to resolve/search across
  the full NSE-listed universe instead of the curated 20. Cached in memory
  with a TTL (`INSTRUMENT_CACHE_TTL_SECONDS`, default 24h).
- **`MARKET_DATA_PROVIDER=yahoo`** -- fetches live-ish quotes for any NSE
  symbol from Yahoo Finance's public chart endpoint, no API key needed
  (`broker_core/market_data_live.py`). Cached briefly
  (`MARKET_DATA_CACHE_TTL_SECONDS`, default 5s) to avoid hammering it.

Both are **best-effort, unofficial, free-tier data sources** -- not a
licensed feed. If a fetch fails (network blocked, rate-limited, endpoint
changed), the app logs a warning and falls back to the seeded data instead
of crashing; it never silently executes an order on missing price data
(orders without a resolvable quote are rejected with a clear reason). Swap
either seam for a licensed vendor / your broker's market-data API in
production by implementing `MarketDataProvider` or `InstrumentRepository`.

The Settings screen shows the active source, instrument count, and last
refresh time, with a manual "Refresh instrument list now" button.

**What this intentionally does *not* do:** suggest what to buy or sell.
Auto-fetching more tickers and real prices is a data-completeness
improvement; recommending trades is a different feature this project
deliberately excludes (see [Core principles](#why-its-built-this-way) and
[`SECURITY.md`](./SECURITY.md)) -- in India, that crosses into SEBI
Registered Investment Advisor / Research Analyst territory.

## API

All endpoints are under `/api/v1`. Interactive docs at `/docs` when the API
is running.

```
POST /api/v1/intent/parse
POST /api/v1/orders/preview
POST /api/v1/orders/confirm
POST /api/v1/orders/{id}/cancel
GET  /api/v1/orders
GET  /api/v1/portfolio
GET  /api/v1/positions
GET  /api/v1/quotes/{symbol}
GET  /api/v1/instruments/search?q=...
GET  /api/v1/instruments/status
POST /api/v1/instruments/refresh
GET  /api/v1/audit-logs
GET  /api/v1/settings
PUT  /api/v1/settings
POST /api/v1/settings/reset-paper-trading
WS   /ws/orders
```

Order confirmation requires an `idempotencyKey`; replaying the same key
returns the original order instead of placing a second one.

## Testing

```bash
# Python: risk engine, AI providers, broker core, and the FastAPI app
cd packages/risk-engine && pip install -e . && pytest
cd packages/ai-providers && pip install -e . && pytest
cd packages/broker-core && pip install -e . && pytest
cd apps/api && pip install -r requirements.txt && pytest

# Frontend unit tests (Vitest + React Testing Library)
cd apps/web && npm install && npm run test

# End-to-end (Playwright; mocks the API network boundary, no backend needed)
cd apps/web && npx playwright install --with-deps chromium && npm run test:e2e
```

## Extending VaaniTrade

- **Add an AI provider**: implement `AIProvider` in `packages/ai-providers`
  (see `mock_provider.py` for the shape) and wire it into
  `ai_providers/factory.py`. Never import a provider SDK from the frontend
  or from `risk-engine`/`broker-core`.
- **Add a real broker**: implement `BrokerAdapter`
  (`packages/broker-core/broker_core/adapter.py`) and swap it in via
  `apps/api/app/deps.py::get_broker`. `PaperBroker` remains the safe
  default.
- **Add a market data or instrument source**: implement `MarketDataProvider`
  or `InstrumentRepository` (`packages/broker-core/broker_core/market_data_provider.py`
  / `instrument_repository.py`) and register it in their `create_*` factory.
  `PaperBroker` only ever depends on the interfaces, so a licensed vendor
  drops in without touching order/risk logic.
- **Add a risk rule**: add a pure function to
  `packages/risk-engine/risk_engine/rules.py` and register it in
  `ALL_RULES`; it is unit-testable with no DB or network involved.
- **Go native**: `packages/voice` and `apps/web/src/services/storage`
  are the only places that touch browser-only APIs. A Capacitor/React
  Native port replaces those two implementations and reuses everything
  else (`shared-types`, hooks, state, and all backend packages) unchanged.

## License

MIT -- see [`LICENSE`](./LICENSE). Contributions welcome; please read
[`CONTRIBUTING.md`](./CONTRIBUTING.md) and [`SECURITY.md`](./SECURITY.md)
first.
