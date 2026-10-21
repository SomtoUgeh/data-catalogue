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

The UI is at [http://localhost:3000](http://localhost:3000). The API is at [http://127.0.0.1:8000](http://127.0.0.1:8000). Vite proxies `/datasets` to FastAPI. The browser always talks to the real API.

Copy `backend/.env.example` and set the three live values below for Jev + Llama. Without them, every create still returns 201. Tags stay empty, the summary is a placeholder, and `curation_status` is `failed`.

Regenerate the typed client after a backend contract change:

```bash
cd frontend && npm run gen:api
```

## Curation

The only curator is the hybrid. TypeSafe Jev (`typesafe/jev`) scores a closed tag set. Llama 3.3 70B writes the one-sentence summary.

Jev is a decision model. It answers one yes/no (`noul`) question per label and returns a probability. That keeps the tag set closed. Llama is a write model. It produces the sentence, validated by PydanticAI `PromptedOutput`.

`TAG_REGISTRY` is the one source of truth for labels. Jev questions, the five-tag cap, and tests all read it. The row keeps the five highest scores at or above 0.55, in probability order.

Failure is part of the contract, not a mock path.

- `ok`: Jev and Llama both succeeded.
- `partial`: exactly one succeeded. Keep the part that worked. Use empty tags or the placeholder summary for the rest.
- `failed`: both failed. The dataset still saves (201) with empty tags and the placeholder summary. The row shows that the AI step failed.

Name, owner, and description are required. A missing or blank field is 400 with `{ "error": "Validation failed", "fields": [{ "field", "message" }] }`.

## Environment

Names only. Never commit values for tokens.

| Name | Role |
| --- | --- |
| `CF_ACCOUNT_ID` | Cloudflare account id for the Workers AI run URL and the AI Gateway URL |
| `CF_AI_GATEWAY_ID` | Gateway id for Llama via `/compat` |
| `CF_AI_GATEWAY_TOKEN` | Optional. Sent as `cf-aig-authorization` if the gateway itself requires auth |
| `LLM_PROVIDER_API_KEY` | Cloudflare API token with Workers AI permission (`Authorization: Bearer`) |
| `LLM_MODEL` | Defaults to `workers-ai/@cf/meta/llama-3.3-70b-instruct-fp8-fast` |
| `CLASSIFIER_MODEL` | Defaults to `typesafe/jev`. Swap to `@cf/cloudflare/clef-flash` for the CF-hosted Jev-compatible model |
| `VITE_API_BASE_URL` | Optional. Leave unset so the browser calls same-origin `/datasets` and Vite proxies to FastAPI |

A live run needs `CF_ACCOUNT_ID`, `CF_AI_GATEWAY_ID`, and `LLM_PROVIDER_API_KEY`.

## Tests

```bash
cd backend && python3 -m pip install -r requirements-dev.txt
cd backend && python3 -m pytest
cd backend && ruff check app tests && ruff format --check app tests
cd backend && mypy app
cd frontend && npm test
cd frontend && npm run typecheck
cd frontend && npm run lint
cd frontend && npm run fmt:check
```

Backend tests stub Jev and Llama at the HTTP boundary. Frontend tests use MSW. The running app does not. Pull requests run the same checks in GitHub Actions.

## Architecture

```
.
├── backend/
│   ├── app/
│   │   ├── main.py                 # app factory, 400/404 handlers, OpenAPI title
│   │   ├── config.py
│   │   ├── schemas.py              # named Dataset / DatasetCreate / ErrorResponse + examples
│   │   ├── routers/datasets.py
│   │   ├── services/dataset_service.py
│   │   ├── repositories/dataset_repository.py
│   │   └── curation/
│   └── scripts/export_openapi.py   # dumps FastAPI's OpenAPI JSON
└── frontend/
    ├── index.html                  # Vite SPA entry
    ├── vite.config.ts              # Router plugin + /datasets → :8000 proxy
    ├── openapi.json                # committed contract snapshot
    ├── openapi-ts.config.ts
    └── src/
        ├── main.tsx                # QueryClientProvider > RouterProvider
        ├── router.tsx              # createRouter({ routeTree, context })
        ├── lib/                    # api base URL, cn()
        ├── components/             # FormField, StatusBanner, PageShell
        ├── components/ui/          # shadcn primitives only
        ├── routes/                 # file routes; loader ensureQueryData
        └── features/datasets/
            ├── api/                # typed client, queryOptions, mutations
            ├── api/generated/      # hey-api output (committed)
            ├── components/
            └── mocks/              # MSW handlers + fixtures (Vitest only)
```

Data flow:

1. `main.tsx` mounts `QueryClientProvider` around `RouterProvider`. `createRouter` receives one `QueryClient` on context, with `defaultPreload: 'intent'` and `defaultPreloadStaleTime: 0` so Query owns caching. There is no SSR.
2. Vite proxies `/datasets` to FastAPI on `:8000`. The typed client uses a same-origin base (`''`) so the browser talks to Vite; FastAPI still allows the Vite origin in CORS for direct calls.
3. The `/` loader calls `context.queryClient.ensureQueryData(datasetsQueryOptions())`. That factory wraps the generated `listDatasets` SDK call.
4. `CataloguePage` reads the same query with `useSuspenseQuery`. Pending and error UI stay on the route (`pendingComponent` / `errorComponent`).
5. Create and delete are `useMutation` hooks. On success they `invalidateQueries` the datasets key. Form values live in TanStack Form; pending and request errors come from the mutation.
6. FastAPI remains the source of truth. `npm run gen:api` exports `/openapi.json` and regenerates the TypeScript SDK plus Zod schemas. The SDK parses successful responses with those schemas. There is no hand-written `fetch`. MSW is for Vitest only.

## Design decisions

**In-memory store.** Fine for the brief. The repository is a class so a database is a swap, not a rewrite. Data resets when the process restarts.

**PydanticAI, not hand-rolled JSON.** The Llama path is an `Agent` with `output_type=PromptedOutput(SummaryResult)` and `retries={'output': 2}`. Field validators require a one-sentence summary under ~25 words starting with `A `. Validation failures go back to the model. Tests use `TestModel` / `FunctionModel` with no network.

**PromptedOutput, not tools.** Workers AI over the gateway `/compat` endpoint is a chat-completions lookalike. Tool calling (`ToolOutput`, the PydanticAI default) is unreliable there. `NativeOutput` needs a provider-native JSON mode we do not want to assume. `PromptedOutput` puts the schema in the prompt and works with any model, including Llama.

**Why the gateway is there.** Cloudflare AI Gateway sits in front of Workers AI so we get request logs, caching, rate limits, and a provider swap (change `LLM_MODEL` from `workers-ai/...` to `openai/...`) without changing application code. `cf-aig-metadata` carries the dataset id so a log line can be traced back to a catalogue row.

**400, not 422.** FastAPI's default validation status is 422. The brief asks for 400 with a descriptive message, so the app factory remaps `RequestValidationError` to `{ "error": "Validation failed", "fields": [{ "field", "message" }] }`.

**@hey-api/openapi-ts, not orval.** The review asked for one well-known generator. Hey API's `@tanstack/react-query` plugin emits `listDatasetsOptions` / mutation helpers that match the Query wiring we already want. The `zod` plugin emits `zDatasetCreate` / `zValidationErrorResponse` from the same spec. The generated folder is committed; run `npm run gen:api` after a schema change.

**MSW for Vitest.** Tests use `setupServer` against the same handlers. No `vi.mock` of an API module. Handlers return the same JSON shapes and 200/201/400/404 codes as FastAPI.

**TanStack Form.** The add form uses the generated `zDatasetCreate` schema, refined for trimmed non-empty name, owner, and description. It is passed as Standard Schema `validators: { onChange, onSubmit }`. Server 400s go through `parseApiError` / `getFieldErrors` and `setFieldMeta`. The create mutation owns pending (`Curating…`) and non-field request errors.

**UI.** Tailwind CSS v4 + shadcn/ui only. Neutral canvas with one blue accent. Inter, then the system sans stack. Desktop is a two-column internal-tool layout: sticky form card on the left, dataset list on the right; they stack on small screens. Tags are Badges (PII uses the warning token). Loader pending uses Skeleton rows. Request errors and failed or partial curation are non-blocking Alerts.

## What I would do next

- Persist to Postgres and add `updated_at`
- Edit a dataset and re-curate
- Auth / team ownership
- Evals on Jev thresholds against a labelled set
