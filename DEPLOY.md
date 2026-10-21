# Deploy the data catalogue on Cloudflare Workers

Local `uvicorn` + Vite stays the take-home default. This file is the Worker path: one Python Worker serves FastAPI and the built SPA on the same origin.

Do not deploy until Somto says so and supplies an account token. Everything below that is marked **local** runs on Miniflare via `uv run pywrangler dev`.

## Why one Worker

Same-origin is the point. The browser keeps calling `/datasets`. Vite already proxies that path in the take-home; the Worker does the same job by handling API routes first and forwarding everything else to the `ASSETS` binding ([Cloudflare's FastAPI + static assets pattern](https://developers.cloudflare.com/workers/languages/python/packages/fastapi/)).

A second Worker for the SPA would need CORS or a service binding. That is extra surface for no gain on this app.

## What runs where

| Path | Store | Summarizer |
| --- | --- | --- |
| `cd backend && uvicorn app.main:app` | In-memory `DatasetRepository` | PydanticAI `LlmCurator` (host default) |
| `cd worker && uv run pywrangler dev` | D1 `D1DatasetRepository` | `HttpLlmCurator` + Pydantic `SummaryResult` |

The hybrid is unchanged: Jev picks tags, Llama writes the summary, `CurationOutcome` is still `ok | partial | failed`.

Python Workers run on Pyodide. `fastapi`, `pydantic`, and `httpx` import. `pydantic-ai` and `httpx2` do not: they are host-only, and the Worker never vendors them. The smallest replacement is the existing prompt + `SummaryResult` validator over the Workers AI binding (or the AI Gateway `/compat` URL when that id is set).

## Bindings

| Binding | Type | Name | Role |
| --- | --- | --- | --- |
| `DB` | D1 | `data-catalogue` | Catalogue rows. In-memory does not survive isolates. |
| `AI` | Workers AI | `AI` | Jev (`typesafe/jev`) and Llama. Used in local `wrangler dev` as a remote binding. |
| `ASSETS` | Static assets | `ASSETS` | Vite `frontend/dist`. |

D1, not KV: the brief is list / insert / delete / monotonic string ids. SQL and `AUTOINCREMENT` match that. KV has no cheap list and no incrementing id.

## Secrets and vars (names only)

Set as **secrets** (`wrangler secret put` / `.dev.vars` locally):

- `LLM_PROVIDER_API_KEY`
- `CF_AI_GATEWAY_TOKEN` (optional; only if the gateway itself requires `cf-aig-authorization`)

Set as **vars** (`wrangler.jsonc` `[vars]` or `.dev.vars`):

- `CF_ACCOUNT_ID`
- `CF_AI_GATEWAY_ID` (optional for the Worker; required for the host PydanticAI Gateway `/compat` path)
- `LLM_MODEL` (default `workers-ai/@cf/meta/llama-3.3-70b-instruct-fp8-fast`)
- `CLASSIFIER_MODEL` (default `typesafe/jev`)

A live Worker curation needs `LLM_PROVIDER_API_KEY` plus the `AI` binding (and `CF_ACCOUNT_ID` if you also want the REST `/ai/run` fallback). The three-value Gateway set is still required for the host FastAPI + PydanticAI path.

Never commit `.dev.vars`.

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

Expect: GET returns the three seeds; POST returns 201 with tags and a summary; DELETE `/datasets/1` returns 200 and the row is gone; missing fields return 400 with `{ "error": "Validation failed", "fields": [...] }`.

The SPA is `http://127.0.0.1:8787/`.

## Deploy (Somto only)

1. `npx wrangler login` (or `CLOUDFLARE_API_TOKEN` with Workers + D1 + Workers AI + AI Gateway permissions).
2. `cd frontend && npm ci && npm run build`
3. `cd ../worker && uv sync --group dev`
4. `uv run pywrangler d1 create data-catalogue` and paste the printed `database_id` into `wrangler.jsonc`.
5. `uv run pywrangler d1 migrations apply data-catalogue --remote`
6. `uv run pywrangler secret put LLM_PROVIDER_API_KEY`
7. Optionally `uv run pywrangler secret put CF_AI_GATEWAY_TOKEN`
8. Set `CF_ACCOUNT_ID` and, if using the Gateway `/compat` URL, `CF_AI_GATEWAY_ID` as vars.
9. `uv run pywrangler deploy`

Do not run step 9 in this prototype.

## Cost note

This app's request volume fits the [Workers Free](https://developers.cloudflare.com/workers/platform/pricing/) request cap (100,000 / day) and the [D1 Free](https://developers.cloudflare.com/d1/platform/pricing/) database (5 million reads / day, 100,000 writes / day, 5 GB).

Workers AI is the part that is not "free forever" in any useful sense. `wrangler dev` already uses the **remote** `AI` binding, so Jev + Llama incur usage even locally. Llama 3.3 70B and `typesafe/jev` are billed per token / neuron. A paid Workers plan plus the Workers AI free allotment is enough to try the demo; treat ongoing curation as a paid AI call, not a Free-tier feature.

## Cold start and latency under `wrangler dev`

Measured on this VM, Miniflare, Python Worker + ~10 MB vendored modules. Not production PoPs.

| Event | Time |
| --- | --- |
| `pywrangler dev` to `Ready on http://0.0.0.0:8787` | about 10–15 s (Pyodide isolate + vendor attach + remote AI session) |
| First `/healthz` after Ready | 147 ms |
| Warm `/healthz` | 9 ms |
| First `GET /datasets` (D1 seed of the three brief rows) | 37 ms |
| Live `POST /datasets` Trade Confirmations (remote Jev + Llama) | 2.65 s, `curation_status=ok` |

Production Workers snapshot Pyodide memory at deploy time, so the 10–15 s local boot is not the production cold-start number. The 2.65 s POST is almost entirely the two remote model calls.
