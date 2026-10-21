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
cd backend && uv run pytest
cd frontend && npm test && npm run typecheck && npm run lint
```

Backend tests run the API with the keyword curator and a fake Workers AI binding. Frontend tests use MSW
handlers that follow the same OpenAPI contract.

## API

| Method | Path | Success | Errors |
| --- | --- | --- | --- |
| `GET` | `/datasets` | `200` list of datasets | |
| `POST` | `/datasets` | `201` saved dataset with `tags` and `summary` | `400` if `name` or `description` is missing or blank |
| `DELETE` | `/datasets/{id}` | `200` deleted dataset | `404` if the id does not exist |

Every error body has `error`. A `400` also lists the invalid fields so the form can show them inline:

```json
{ "error": "Validation failed", "fields": [{ "field": "name", "message": "name is required" }] }
```

A dataset has `id`, `name`, `owner`, `description`, `tags`, `summary`, and `curation_status` (`"ok"` or `"failed"`).

The frontend client is generated from the OpenAPI document. After a backend contract change:

```bash
cd frontend && npm run gen:api
```

## Structure

```
backend/
  src/app/
    main.py                 app setup, 400 and 404 handlers, local wiring
    schemas.py              request, response, and error models
    routers/datasets.py     HTTP layer: routes, status codes, OpenAPI operation ids
    services/               business logic: create with curation, delete
    repositories/           DatasetStore protocol, in-memory store, D1 store, seed data
    curation/               Curator protocol, keyword curator, Workers AI curator
    cloudflare.py           Python/JavaScript value conversion for Cloudflare bindings
  src/worker.py             Cloudflare Worker entry: binds D1 and Workers AI to the app
  migrations/               D1 schema and seed rows
  scripts/export_openapi.py prints the OpenAPI document for the frontend generator
  wrangler.jsonc            Worker, D1, Workers AI, and static asset config
frontend/src/
  features/datasets/
    api/generated/          typed client, zod schemas, and query keys from openapi.json
    api/                    query options, mutations, error parsing, form schema
    components/             catalogue page, add form, list, row, tags, banners
    mocks/                  MSW handlers for tests
  components/               form field, status banner, shadcn ui primitives
  routes/                   TanStack Router file routes
```

## Deployment

One Cloudflare Worker serves the API and the built frontend from the same origin.
The Python Worker handles `/datasets`, `/docs`, and `/openapi.json`; every other path is served from
`frontend/dist` as static assets. Storage is a D1 (SQLite) database and curation calls Workers AI
(Llama 3.3 70B), both through bindings, so no API keys are needed.

```bash
cd frontend && npm ci && npm run build
cd ../backend
uv sync --group dev
uv run pywrangler d1 migrations apply data-catalogue --remote   # first deploy only
uv run pywrangler deploy
```

To run the Worker locally against a local D1 (Workers AI is still remote):

```bash
cd backend
uv run pywrangler d1 migrations apply data-catalogue --local
uv run pywrangler dev
```

## Design notes

- **One app, two wirings.** `create_app` takes a `DatasetService`. `main.py` wires the in-memory store and
  keyword curator for local runs. `worker.py` overrides the service dependency per request with the D1 store
  and Workers AI curator from the Worker environment. Routes, service, and schemas are shared.
- **Layers.** Routes only handle HTTP. `DatasetService` holds the logic. The store protocol is the only
  thing that touches storage, so swapping memory for D1 is one class.
- **Validation.** Pydantic rejects missing or blank `name` and `description`. FastAPI returns `422` by
  default, so one handler changes this to `400` with a field list.
- **Curation failure.** The service catches any curation error (network, timeout, invalid model output) and
  logs it. The dataset still saves with empty `tags` and `summary` and `curation_status: "failed"`. The UI
  shows this on the form and on the row.
- **LLM output.** The Workers AI request uses JSON mode with the `CurationResult` schema, and the reply is
  validated against the same schema. The prompt asks for 3–6 tags in fixed categories, one sentence of at
  most 25 words, and gives two worked examples from the sample data.
- **Keyword mock.** A table maps keywords to domain tags. PII is added for personal identifiers, or for a
  `name` field in a dataset about people, so "product name" does not count. Cadence comes from words like
  "daily". The summary is built from the field list in the description's first sentence.
- **Frontend state.** TanStack Query owns the list. Add and delete mutations invalidate it, so the page
  updates without a reload. Components never call `fetch` directly; they use the generated client.
