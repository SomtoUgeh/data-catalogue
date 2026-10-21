# Data Catalogue

Register datasets and get AI-generated tags and a one-sentence summary for each one.
FastAPI backend, React (Vite) frontend, one Cloudflare Worker in production.

**Live:** https://data-catalogue.somto.workers.dev · **API docs:** https://data-catalogue.somto.workers.dev/docs

## Run locally

Requires Python 3.12+ with [uv](https://docs.astral.sh/uv/), and Node 22+.

```bash
# Terminal 1: API on http://127.0.0.1:8000 (docs at /docs)
cd backend
uv run uvicorn app.main:app --app-dir src --reload

# Terminal 2: UI on http://127.0.0.1:3000
cd frontend
npm install
npm run dev
```

Locally the catalogue uses an in-memory store seeded with the three sample datasets, and a keyword-based
curator that needs no API key. The Vite dev server forwards `/datasets` to the API, so no CORS setup is needed.

## Test

```bash
cd backend && uv run pytest && uv run pyright -p ../pyrightconfig.json
cd frontend && npm test && npm run typecheck && npm run lint && npm run fmt:check
```

Backend tests run the API with the keyword curator and a fake Workers AI binding. Frontend tests use MSW
handlers that follow the same OpenAPI contract.

## API

| Method | Path | Success | Errors |
| --- | --- | --- | --- |
| `GET` | `/datasets?limit=50&before={id}` | `200` page of datasets, newest first | `400` if `limit` is outside 1–100 or `before` is not an id |
| `POST` | `/datasets` | `201` saved dataset with `tags` and `summary` | `400` if `name` or `description` is missing or blank, a field is too long, or the body is not a JSON object; `429` |
| `DELETE` | `/datasets/{id}` | `200` deleted dataset | `404` if the id does not exist; `429` |

- **Paging.** `limit` defaults to 50. To get the next page, pass the last id of the current page as
  `before`. A page shorter than `limit` is the last one. Pages use the primary key (keyset pagination), so a
  deep page costs the same as the first, and an insert or delete never shifts or repeats rows.
- **Tags.** Tags come only from the vocabulary in `backend/src/app/curation/tags.py`, so `tags` is empty
  when nothing fits the description. The UI then shows "No tags matched this description." A failed
  curation is shown as a warning instead.
- **Input.** `name` and `description` are required; `owner` is optional. Limits: `name` and `owner` 200
  characters, `description` 2000.
- **Rate limit.** On Cloudflare, `POST` and `DELETE` return `429` with `Retry-After: 60` after 10 requests in
  a minute from one IP.

Every error body has `error`, including unknown paths (`404`), wrong methods (`405`), and `500`. A `400`
also lists the invalid fields so the form can show them inline:

```json
{ "error": "Validation failed", "fields": [{ "field": "name", "message": "Name is required" }] }
```

Field messages are `<Field> is required`, `<Field> must be at most <n> characters`, `Before must be a
dataset id`, or `Request body must be a JSON object` (with `field: "body"`). Other type errors read
`<Field>: <Pydantic message>`. A `500` never includes internal details; the traceback goes to the logs.

A dataset has `id`, `name`, `owner`, `description`, `tags`, `summary`, and `curation_status` (`"ok"` or `"failed"`).

The frontend client is generated from the OpenAPI document. After a backend contract change:

```bash
cd frontend && npm run gen:api
```

## Structure

```
backend/
  src/app/                  the FastAPI application; runtime-neutral, no Cloudflare imports
    main.py                 create_app and the local wiring (in-memory store, keyword curator)
    logs.py                 one-line JSON log events
    schemas.py              request, response, and error models
    api/                    HTTP layer
      datasets.py           routes for /datasets, with OpenAPI operation ids
      dependencies.py       get_service, the dependency the Worker overrides
      errors.py             400, 404, 405, and 500 handlers; every error is {"error": ...}
    services/datasets.py    business logic: list a page, create with curation, delete
    repositories/           DatasetStore protocol, in-memory store, D1 store, seed data
    curation/
      base.py               Curator protocol, CurationResult, IncompleteCurationError
      tags.py               the tag vocabulary: id, meaning for Clef, keywords for the mock
      prompts.py            summary instructions for the chat model
      workers_ai.py         Clef picks tags, Llama writes the summary; deadline, retry, AI Gateway, log event
      keyword.py            rule-based mock for local runs and tests
  src/worker.py             Cloudflare Worker entry: binds D1 and Workers AI, limits writes, logs to the console
  tests/                    API, curator, and error-shape tests; payloads.py holds shared bodies
  migrations/               D1 schema and seed rows
  scripts/export_openapi.py prints the OpenAPI document for the frontend generator
  wrangler.jsonc            Worker, D1, Workers AI, AI Gateway, rate limit, observability, and asset config
frontend/src/
  features/datasets/
    api/generated/          typed client, zod schemas, and query keys from openapi.json
    api/                    query options, mutations, error parsing, form schema
    components/             catalogue page, add form, paged list, row, tags, banners
    mocks/                  MSW handlers and store for tests, with the same paging as the API
  components/               form field, status banner, shadcn ui primitives
  lib/                      class-name helper
  routes/                   TanStack Router file routes
  test/                     test setup and render helpers
```

`src/` is the folder pywrangler bundles into the Worker, so tests, scripts, and migrations never ship.

## How it fits together

**Adding a dataset**, from the click to the saved row:

1. `AddDatasetForm.tsx` validates the fields with `api/formSchema.ts` (the generated Zod schema plus form
   messages), then runs the create mutation from `api/mutations.ts`.
2. The mutation calls `createDataset` from the generated client (`api/generated/sdk.gen.ts`).
   `api/errors.ts` (`unwrapResponse`) turns any failure into an `ApiError` the form can show.
3. On Cloudflare the request reaches `src/worker.py`: `WriteRateLimit` checks the per-IP limit, and
   `service_from_env` builds a `DatasetService` from this request's D1 and Workers AI bindings.
   Locally, uvicorn serves `app/main.py`, which uses the in-memory store and the keyword curator instead.
4. `app/api/datasets.py` receives the request. FastAPI validates the body against `DatasetCreate` in
   `app/schemas.py`; invalid input goes to `app/api/errors.py` and comes back as a `400`.
5. `app/services/datasets.py` asks the curator for tags and a summary:
   `app/curation/workers_ai.py` calls Clef, then Llama, using `tags.py` and `prompts.py`, and logs one
   `curation` event. If curation fails, the service keeps any tags and marks the dataset `failed`.
6. The service saves through the store (`app/repositories/d1.py` on Cloudflare) and returns the dataset
   with a `201`.
7. Back in the browser, the mutation invalidates the list query, so the list refetches and the new
   dataset appears at the top.

**Loading the page:** `routes/index.tsx` runs `api/queryOptions.ts` before render, which calls
`GET /datasets?limit=50`. `CataloguePage.tsx` reads that data, and "Load more datasets" fetches the next
page with `before` set to the last id shown.

**Keeping both sides in step:** the API's Pydantic models produce the OpenAPI document. `npm run gen:api`
turns it into the frontend's types, Zod schemas, client, and query keys. After you regenerate, frontend
code that no longer matches the API fails `npm run typecheck`.

## Deployment

One Cloudflare Worker serves the API and the built frontend from the same origin.
The Python Worker handles `/datasets`, `/docs`, and `/openapi.json`; every other path is served from
`frontend/dist` as static assets. Storage is a D1 (SQLite) database and curation calls Workers AI,
both through bindings, so no API keys are needed.

```bash
cd frontend && npm ci && npm run build
cd ../backend
uv sync --group dev
uv run pywrangler d1 migrations apply data-catalogue --remote   # first deploy only
uv run pywrangler deploy
```

### Configuration

Everything the Worker needs is in `backend/wrangler.jsonc`, committed. There are no secrets: the `DB`
and `AI` bindings connect the Worker to D1 and Workers AI in the Cloudflare account, so no keys are
stored.

| Name | Kind | Purpose |
| --- | --- | --- |
| `DB` | D1 binding | The `datasets` table |
| `AI` | Workers AI binding | Runs both models |
| `WRITE_LIMITER` | Rate limit binding | 10 writes per minute per IP |
| `CLASSIFIER_MODEL` | var | Chooses the tags (`@cf/cloudflare/clef-flash`) |
| `SUMMARY_MODEL` | var | Writes the summary (`@cf/meta/llama-3.3-70b-instruct-fp8-fast`) |
| `AI_GATEWAY_ID` | var | AI Gateway that logs model calls (`default`). Remove it to call Workers AI directly. |

To try another model without editing the file, add `--var SUMMARY_MODEL:<model>` to `pywrangler dev`.
A real secret, if one is added later, goes in `backend/.dev.vars` locally (not committed) and is set with
`uv run pywrangler secret put <NAME>` in production. The free Workers AI allowance is daily. When it runs
out, calls fail with error 3036 and datasets save as `curation_status: "failed"`.

To run the Worker locally against a local D1, log in first (`npx wrangler login`), because Workers AI
always runs remotely:

```bash
cd backend
uv run pywrangler d1 migrations apply data-catalogue --local
uv run pywrangler dev
```

## Observability and debugging

On Cloudflare, three sources describe each request. `observability` in `wrangler.jsonc` turns on the first
two, and the `AI_GATEWAY_ID` var the third.

| Source | What it records | Where |
| --- | --- | --- |
| Workers Logs | One log per request, plus our JSON events | Dashboard → Workers → data-catalogue → Logs |
| Traces | A span per request, per D1 query (`d1_all`, `d1_first`), and per AI call (`fetch`), with timings | Dashboard → Workers → data-catalogue → Traces |
| AI Gateway | Each model call: prompt, response, latency, and tokens | Dashboard → AI → AI Gateway → `default` → Logs |

Events (`app/logs.py`) are one JSON object per line. Workers Logs keeps each line as one entry, and
`worker.py` writes events to the console as objects at the matching level, so their fields are searchable.

| Event | Level | Fields |
| --- | --- | --- |
| `curation` | info if `outcome` is `ok`, else warning | `curation_id`, `dataset`, both models, `outcome` (`ok`, `incomplete`, `failed`), `error`, `classify_ms`, `summary_ms`, `*_retried_after`, `scores` (Clef's top 8, including tags under the threshold), `tags`, `summary_words` |
| `curation_incomplete` / `curation_failed` | warning / error | `dataset`, `tags`, `traceback` |
| `unhandled_error` | error | `method`, `path`, `traceback` |

To find out why a dataset got the tags or summary it did:

1. In Workers Logs, filter on `event = curation` and the dataset name.
2. Read `outcome`, `error`, and `scores`. `scores` shows how close the missing tags came to 0.55.
3. Copy `curation_id`. In AI Gateway logs, filter on metadata `curation_id` to see the exact prompts and
   model replies for both steps (`step` is `classify` or `summary`).

`pywrangler dev` records the same logs and spans locally. Query them with
`POST http://localhost:8787/cdn-cgi/local/explorer/api/local/observability/query`, for example
`{"sql": "SELECT name, duration_ms FROM spans ORDER BY start_ms DESC LIMIT 20"}`. Under uvicorn, events
are printed to stdout.
