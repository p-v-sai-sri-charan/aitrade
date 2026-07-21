# Contributing to VaaniTrade

Thanks for your interest in contributing! VaaniTrade is an open-source,
paper-trading-only voice assistant for Indian markets. This document covers
local setup and contribution guidelines.

## Project layout

```
vaanitrade/
├── apps/
│   ├── web/            # Vite + React + TS PWA
│   └── api/             # FastAPI backend
├── packages/
│   ├── shared-types/     # TypeScript types shared by web (and future RN app)
│   ├── voice/            # VoiceService interface + browser implementation
│   ├── ai-providers/     # Python: provider-neutral AIProvider interface + adapters
│   ├── risk-engine/       # Python: deterministic risk rules (pure, unit tested)
│   └── broker-core/       # Python: BrokerAdapter interface + PaperBroker
```

## Local development

See `README.md` for full setup instructions (Docker and non-Docker).

## Development principles (please read before opening a PR)

1. **No autonomous trading.** Never add a code path that places an order
   without an explicit user confirmation step.
2. **No stock recommendations.** The assistant extracts and executes
   instructions; it must not suggest what to buy/sell.
3. **AI is provider-neutral and sandboxed.** New AI logic belongs in
   `packages/ai-providers` behind the `AIProvider` protocol. Never import a
   specific provider SDK from `apps/web`, routers, or the risk/broker
   packages.
4. **Validate, don't trust.** Anything coming from an AI provider or the
   client must be re-validated against the Pydantic/Zod schemas before use.
5. **Deterministic risk checks stay deterministic.** `packages/risk-engine`
   must not call any network or AI service.
6. **Mobile-first.** UI changes should be tested at 360px width and use
   touch-friendly (44px+) targets.

## Tests

- Frontend: `npm run test` (Vitest) and `npm run test:e2e` (Playwright) in `apps/web`.
- Backend: `pytest` in `apps/api` (also runs `risk-engine`/`ai-providers`/`broker-core` tests if installed editable).

Please add or update tests for any behavioral change, especially to the risk
engine, instrument resolver, or order confirmation flow.

## Commit style

Use clear, imperative commit messages (e.g. `Add duplicate-order risk rule`).
Keep PRs focused; explain the "why" in the description.

## Code of conduct

Be respectful and constructive. This project handles financial workflows —
extra care and review is expected for anything touching order placement or
risk checks.
