# Data Catalogue

A small data-catalogue app: register a dataset, get tags and a one-sentence summary, browse and delete entries.

Somto's Macquarie take-home. Built so the Friday front-end architecture discussion can walk the request path without extra ceremony.

## Run

Backend (from `backend/`):

```bash
python3 -m pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```

Frontend (from `frontend/`):

```bash
npm install
npm run dev
```

The UI is at [http://localhost:3000](http://localhost:3000). The API is at [http://127.0.0.1:8000](http://127.0.0.1:8000).

Copy `backend/.env.example` only if you want a live LLM run. Leave it unset for the default keyword mock.

## Environment

Names only — never commit values for tokens.

| Name | Role |
| --- | --- |
| `CF_ACCOUNT_ID` | Cloudflare account id for the AI Gateway URL |
| `CF_AI_GATEWAY_ID` | Gateway id |
| `CF_AI_GATEWAY_TOKEN` | Optional. Sent as `cf-aig-authorization` if the gateway itself requires auth |
| `LLM_PROVIDER_API_KEY` | Cloudflare API token with Workers AI permission (`Authorization: Bearer`) |
| `LLM_MODEL` | Defaults to `workers-ai/@cf/meta/llama-3.3-70b-instruct-fp8-fast` |
| `CURATOR` | `mock` (force keyword), `llm` (use gateway if configured), `fail` (demo fallback) |
| `API_BASE_URL` | FastAPI origin used by TanStack Start server functions. Defaults to `http://127.0.0.1:8000` |
| `VITE_API_BASE_URL` | Browser fallback for the same origin |

A live LLM run needs `CF_ACCOUNT_ID`, `CF_AI_GATEWAY_ID`, and `LLM_PROVIDER_API_KEY`. The validation pass uses the mock.

## Tests

```bash
cd backend && python3 -m pytest
cd frontend && npm test
```

## Architecture

```
.
├── backend/
│   ├── app/
│   │   ├── main.py                 # app factory, 400/404 handlers
│   │   ├── config.py               # pydantic-settings
│   │   ├── schemas.py
│   │   ├── routers/datasets.py     # HTTP only
│   │   ├── services/dataset_service.py
│   │   ├── repositories/dataset_repository.py
│   │   └── curation/
│   │       ├── base.py             # Curator + CurationError
│   │       ├── keyword.py          # default mock
│   │       ├── llm.py              # PydanticAI + Cloudflare AI Gateway
│   │       ├── tags.py
│   │       └── factory.py
│   └── tests/
└── frontend/
    └── src/
        ├── api/datasets.ts         # FastAPI HTTP client
        ├── api/datasetFns.ts       # Start server functions
        ├── components/             # form, list, row, page
        └── routes/index.tsx        # loader, pending, error, invalidate
```

Request path:

1. The `/` route loader calls `fetchDatasets()` (a Start server function).
2. That function uses `src/api/datasets.ts` to `GET /datasets` on FastAPI.
3. FastAPI: router → service → repository. On create, the service asks a `Curator` for tags and a summary.
4. After add/delete the page calls `router.invalidate()`, which re-runs the loader. No full reload.

## Design decisions

**In-memory store.** Fine for the brief. The repository is a class so a database is a swap, not a rewrite. Data resets when the process restarts.

**Mock vs LLM.** The keyword curator is the default. It is a rule table (domain, cadence, PII), not a single hardcoded string. Trade Confirmations lands on tags close to `trading, finance, settlements, daily`. The LLM path is opt-in when gateway config and `LLM_PROVIDER_API_KEY` are set.

**PydanticAI, not hand-rolled JSON.** The LLM curator is an `Agent` with `output_type=PromptedOutput(CurationResult)` and `retries={'output': 2}`. Field validators normalise tags (lowercase, acronyms, dedupe, punctuation, cap 6) and require a one-sentence summary under ~25 words starting with `A `. Validation failures go back to the model. Tests use `TestModel` / `FunctionModel` with no network.

**PromptedOutput, not tools.** Workers AI over the gateway `/compat` endpoint is a chat-completions lookalike. Tool calling (`ToolOutput`, the PydanticAI default) is unreliable there. `NativeOutput` needs a provider-native JSON mode we do not want to assume. `PromptedOutput` puts the schema in the prompt and works with any model, including Llama. That is why it is the mode.

**Why the gateway is there.** Cloudflare AI Gateway sits in front of Workers AI so we get request logs, caching, rate limits, and a provider swap (change `LLM_MODEL` from `workers-ai/...` to `openai/...`) without changing application code. `cf-aig-metadata` carries the dataset id so a log line can be traced back to a catalogue row.

**400, not 422.** FastAPI's default validation status is 422. The brief asks for 400 with a descriptive message, so the app factory remaps `RequestValidationError`.

**Curation fallback.** If the agent raises (`UnexpectedModelBehavior`, timeout, HTTP error, or anything else), the dataset still saves with placeholder tags/summary and `curation_status: "failed"`. The form and the row show that to the user. `CURATOR=fail` forces this path for a demo.

**Server functions as the loader boundary.** Start server functions keep the FastAPI URL on the server for the first paint. Mutations go through the same `datasets.ts` service so `CataloguePage` stays a regular component and Vitest can mock the module. Both paths share one HTTP client.

**TanStack Form.** Field-level `onSubmit` validators for empty name/description, `isSubmitting` for the button, and server 400 messages mapped back onto the field.

## What I would do next

- Persist to Postgres and add `updated_at`
- Edit a dataset and re-curate
- Auth / team ownership
- Evals on the curator (the mock is good enough to ship a review build; the LLM path needs golden examples)
- Drop `CURATOR=fail` once there is a real staging key
