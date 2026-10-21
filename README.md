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

Frontend-only (no FastAPI process): set `VITE_API_MOCKING=true` so the MSW worker answers with the same shapes and status codes.

Regenerate the typed client after a backend contract change:

```bash
cd frontend && npm run gen:api
```

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
| `VITE_API_BASE_URL` | Optional. Leave unset so the browser calls same-origin `/datasets` and Vite proxies to FastAPI. Set only to hit FastAPI directly. |
| `VITE_API_MOCKING` | `true` starts the MSW worker for frontend-only demos |

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
            └── mocks/              # MSW handlers + fixtures
```

Data flow:

1. `main.tsx` mounts `QueryClientProvider` around `RouterProvider`. `createRouter` receives one `QueryClient` on context, with `defaultPreload: 'intent'` and `defaultPreloadStaleTime: 0` so Query owns caching. There is no SSR.
2. Vite proxies `/datasets` to FastAPI on `:8000`. The typed client uses a same-origin base (`''`) so the browser talks to Vite; FastAPI still allows the Vite origin in CORS for direct calls.
3. The `/` loader calls `context.queryClient.ensureQueryData(datasetsQueryOptions())`. That factory wraps the generated `listDatasets` SDK call.
4. `CataloguePage` reads the same query with `useSuspenseQuery`. Pending and error UI stay on the route (`pendingComponent` / `errorComponent`).
5. Create and delete are `useMutation` hooks. On success they `invalidateQueries` the datasets key. Form values live in TanStack Form; pending and request errors come from the mutation.
6. FastAPI remains the source of truth. `npm run gen:api` exports `/openapi.json` and regenerates the TypeScript SDK plus Zod schemas. The SDK parses successful responses with those schemas. There is no hand-written `fetch`. MSW mirrors the same contract in Vitest and, when `VITE_API_MOCKING=true`, in the browser.

## Design decisions

**In-memory store.** Fine for the brief. The repository is a class so a database is a swap, not a rewrite. Data resets when the process restarts.

**Mock vs LLM.** The keyword curator is the default. It is a rule table (domain, cadence, PII), not a single hardcoded string. Trade Confirmations lands on tags close to `trading, finance, settlements, daily`. The LLM path is opt-in when gateway config and `LLM_PROVIDER_API_KEY` are set.

**PydanticAI, not hand-rolled JSON.** The LLM curator is an `Agent` with `output_type=PromptedOutput(CurationResult)` and `retries={'output': 2}`. Field validators normalise tags (lowercase, acronyms, dedupe, punctuation, cap 6) and require a one-sentence summary under ~25 words starting with `A `. Validation failures go back to the model. Tests use `TestModel` / `FunctionModel` with no network.

**PromptedOutput, not tools.** Workers AI over the gateway `/compat` endpoint is a chat-completions lookalike. Tool calling (`ToolOutput`, the PydanticAI default) is unreliable there. `NativeOutput` needs a provider-native JSON mode we do not want to assume. `PromptedOutput` puts the schema in the prompt and works with any model, including Llama. That is why it is the mode.

**Why the gateway is there.** Cloudflare AI Gateway sits in front of Workers AI so we get request logs, caching, rate limits, and a provider swap (change `LLM_MODEL` from `workers-ai/...` to `openai/...`) without changing application code. `cf-aig-metadata` carries the dataset id so a log line can be traced back to a catalogue row.

**400, not 422.** FastAPI's default validation status is 422. The brief asks for 400 with a descriptive message, so the app factory remaps `RequestValidationError` to `{ "error": "Validation failed", "fields": [{ "field", "message" }] }`. The top-level `error` string stays so a 400 is still obvious; `fields` is how the form maps messages without regex.

**Curation fallback.** If the agent raises (`UnexpectedModelBehavior`, timeout, HTTP error, or anything else), the dataset still saves with placeholder tags/summary and `curation_status: "failed"`. The form and the row show that to the user. `CURATOR=fail` forces this path for a demo.

**@hey-api/openapi-ts, not orval.** The review asked for one well-known generator. Hey API's `@tanstack/react-query` plugin emits `listDatasetsOptions` / mutation helpers that match the Query wiring we already want. The `zod` plugin emits `zDatasetCreate` / `zValidationErrorResponse` from the same spec; the SDK `validator` option parses successful responses against those schemas. Pydantic `min_length=1` + `str_strip_whitespace` on `DatasetCreate` is what OpenAPI publishes as `minLength: 1`, so the generated Zod rules mirror FastAPI. Orval's MSW plugin would have generated handlers too; we wrote those by hand so they can stay aligned with FastAPI's 400 body, seeded rows, and keyword-like tags. The generated folder is committed; run `npm run gen:api` after a schema change.

**MSW for tests and optional browser demos.** Vitest uses `setupServer` against the same handlers as the opt-in worker. No `vi.mock` of an API module. Handlers return the same JSON shapes and 200/201/400/404 codes as FastAPI.

**TanStack Form.** The add form uses the generated `zDatasetCreate` schema, refined for trimmed non-empty name/description (`Name is required`). It is passed as Standard Schema `validators: { onChange, onSubmit }` — no adapter. Server 400s go through `parseApiError` / `getFieldErrors` (safeParse, never a raw `ZodError`) and `setFieldMeta`. The create mutation owns pending (`Curating…`) and non-field request errors.

**UI.** Tailwind CSS v4 + shadcn/ui only — no leftover plain CSS classes. Neutral canvas with one blue accent. Inter, then the system sans stack. Desktop is a two-column internal-tool layout: sticky form card on the left, dataset list on the right; they stack on small screens. Tags are Badges (PII uses the warning token). Loader pending uses Skeleton rows; an empty catalogue is a quiet card. Request errors and the curation fallback are non-blocking Alerts. Focus rings stay visible; motion respects `prefers-reduced-motion`. Dark tokens follow `prefers-color-scheme` only.

## What I would do next

- Persist to Postgres and add `updated_at`
- Edit a dataset and re-curate
- Auth / team ownership
- Evals on the curator (the mock is good enough to ship a review build; the LLM path needs golden examples)
- Drop `CURATOR=fail` once there is a real staging key
