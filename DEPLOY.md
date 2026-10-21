# Deploy the data catalogue on Cloudflare Workers

Local `uvicorn` + Vite stays the take-home default. This file is the Worker path: one Python Worker serves FastAPI and the built SPA on the same origin.

Do not deploy until Somto says so and supplies an account token. Everything below that is marked **local** runs on Miniflare via `uv run pywrangler dev`.

## Why one Worker

Same-origin is the point. The browser keeps calling `/datasets`. Vite already proxies that path in the take-home; the Worker does the same job by handling API routes first and forwarding everything else to the `ASSETS` binding ([Cloudflare's FastAPI + static assets pattern](https://developers.cloudflare.com/workers/languages/python/packages/fastapi/)).

A second Worker for the SPA would need CORS or a service binding. That is extra surface for no gain on this app.

## What runs where

| Path | Store | Summarizer |
| --- | --- | --- |
| `cd backend && uvicorn app.main:app` | In-memory `DatasetRepository` | PydanticAI `LlmCurator` |
| `cd worker && uv run pywrangler dev` | D1 `D1DatasetRepository` | The same `LlmCurator` |

The hybrid is unchanged: Jev picks tags, Llama writes the summary, `CurationOutcome` is still `ok | partial | failed`.

Python Workers run on Pyodide. `pydantic-ai-slim[openai]==2.59.0` vendors as pure-Python plus Pyodide wasm wheels (`pydantic-core`, `tiktoken`, `jiter`). `httpx2` uses `httpx2-jsfetch` (`AsyncJavascriptFetchTransport`) so `Agent.run_sync` goes through JS `fetch`.

`openai` calls `os.urandom` at import time. Workers forbid that during isolate startup, so `LlmCurator` imports PydanticAI inside the methods that run after the first request, not at module load. `PYDANTIC_AI_NO_BANNER=1` keeps the Logfire setup banner out of wrangler logs.

## Bindings

| Binding | Type | Name | Role |
| --- | --- | --- | --- |
| `DB` | D1 | `data-catalogue` | Catalogue rows. In-memory does not survive isolates. |
| `AI` | Workers AI | `AI` | Jev (`typesafe/jev`) only. Used in local `wrangler dev` as a remote binding. |
| `ASSETS` | Static assets | `ASSETS` | Vite `frontend/dist`. |

D1, not KV: the brief is list / insert / delete / monotonic string ids. SQL and `AUTOINCREMENT` match that. KV has no cheap list and no incrementing id.

Llama does not use `env.AI`. The summary is an OpenAI-compatible HTTP call so host and Worker share one `LlmCurator` and Gateway can still see the request when a gateway id is set.

## Secrets and vars (names only)

Set as **secrets** (`wrangler secret put` / `.dev.vars` locally):

- `LLM_PROVIDER_API_KEY`
- `CF_AI_GATEWAY_TOKEN` (optional; only if the gateway itself requires `cf-aig-authorization`)

Set as **vars** (`wrangler.jsonc` `[vars]` or `.dev.vars`):

- `CF_ACCOUNT_ID`
- `CF_AI_GATEWAY_ID` (optional on the Worker). When set, Llama uses AI Gateway `.../compat`. When unset, Llama uses Workers AI REST `.../ai/v1`.
- `LLM_MODEL` (default `workers-ai/@cf/meta/llama-3.3-70b-instruct-fp8-fast`)
- `CLASSIFIER_MODEL` (default `typesafe/jev`)
- `PYDANTIC_AI_NO_BANNER` (`1` on the Worker)

A live Worker summary needs `LLM_PROVIDER_API_KEY` and `CF_ACCOUNT_ID`. Jev on the Worker also needs the `AI` binding. The host FastAPI + Gateway path still wants the three-value Gateway set (`CF_ACCOUNT_ID`, `CF_AI_GATEWAY_ID`, `LLM_PROVIDER_API_KEY`).

Never commit `.dev.vars`.

## Gateway `/compat`

Cloudflare now marks `/compat` as deprecated for new single-model chat and points at REST `/ai/v1/chat/completions` ([Unified API](https://developers.cloudflare.com/ai-gateway/usage/chat-completion/)). This app keeps `/compat` when a gateway id is set. That is still the OpenAI-compatible Gateway URL the host README documents, and `OpenAIProvider` posts to `{base}/chat/completions`. A different Gateway provider path was not live-proved, so it was not swapped.

## Local (Miniflare)

Needs Node, `uv`, and a built SPA. From the repo root:

```bash
cd frontend && npm ci && npm run build
cd ../worker
cp .dev.vars.example .dev.vars   # fill names from the table above
uv sync --group dev
uv run pywrangler d1 migrations apply data-catalogue --local
uv run pywrangler dev --ip 127.0.0.1 --port 8787
```

`pywrangler dev` vendors `../backend` into `python_modules/` (gitignored) and refuses to run next to `backend/requirements.txt`, which is why the Worker project lives in `worker/`.

Checklist against `http://127.0.0.1:8787`:

```bash
curl -sS http://127.0.0.1:8787/datasets
curl -sS -D- http://127.0.0.1:8787/datasets \
  -H 'Content-Type: application/json' \
  -d '{"name":"Trade Confirmations","owner":"Middle Office","description":"Daily export of confirmed trades including instrument type, counterparty, notional value, and settlement date."}'
curl -sS -X DELETE http://127.0.0.1:8787/datasets/1
curl -sS -D- http://127.0.0.1:8787/datasets \
  -H 'Content-Type: application/json' \
  -d '{}'
```

Expect: GET returns the three seeds; POST returns 201 with tags and a summary from PydanticAI; DELETE `/datasets/1` returns 200 and the row is gone; missing fields return 400 with `{ "error": "Validation failed", "fields": [...] }`.

The SPA is `http://127.0.0.1:8787/`.

## Deploy (Somto only)

1. `npx wrangler login` (or `CLOUDFLARE_API_TOKEN` with Workers + D1 + Workers AI + AI Gateway permissions).
2. `cd frontend && npm ci && npm run build`
3. `cd ../worker && uv sync --group dev`
4. `uv run pywrangler d1 create data-catalogue` and paste the printed `database_id` into `wrangler.jsonc`.
5. `uv run pywrangler d1 migrations apply data-catalogue --remote`
6. `uv run pywrangler secret put LLM_PROVIDER_API_KEY`
7. Optionally `uv run pywrangler secret put CF_AI_GATEWAY_TOKEN`
8. Set `CF_ACCOUNT_ID` and, if you want Gateway logs on Llama, `CF_AI_GATEWAY_ID` as vars.
9. `uv run pywrangler deploy`

Do not run step 9 in this prototype.

## Cost note

This app's request volume fits the [Workers Free](https://developers.cloudflare.com/workers/platform/pricing/) request cap (100,000 / day) and the [D1 Free](https://developers.cloudflare.com/d1/platform/pricing/) database (5 million reads / day, 100,000 writes / day, 5 GB).

Workers AI is the part that is not "free forever" in any useful sense. `wrangler dev` already uses the **remote** `AI` binding for Jev, and Llama is an HTTP call to Workers AI or the Gateway. Llama 3.3 70B and `typesafe/jev` are billed per token / neuron. A paid Workers plan plus the Workers AI free allotment is enough to try the demo; treat ongoing curation as a paid AI call, not a Free-tier feature.

## Bundle size and cold start under `wrangler dev`

Measured on this VM, Miniflare. Not production PoPs.

| | Before (`HttpLlmCurator`, no pydantic-ai) | After (`pydantic-ai-slim[openai]==2.59.0`) |
| --- | --- | --- |
| `worker/python_modules` | 12 MB | 44 MB |
| Wrangler attached vendored modules | 9,996 KiB | 34,368 KiB |
| `pywrangler dev` to Ready | about 10–15 s | about 15 s |
| First `/healthz` after Ready | 147 ms | 169 ms |
| Warm `/healthz` | 9 ms | 10 ms |
| First `GET /datasets` | 37 ms | 28 ms |
| Live `POST /datasets` Trade Confirmations | 2.65 s, `curation_status=ok` (env.AI Llama) | 4.03 s, `curation_status=ok` (PydanticAI HTTP) |

Production Workers snapshot Pyodide memory at deploy time, so the local boot is not the production cold-start number. The POST is almost entirely the two remote model calls.
