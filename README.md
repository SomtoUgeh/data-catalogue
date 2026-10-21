# Data Catalogue

Register datasets and get AI-generated tags and a one-sentence summary for each one.
FastAPI backend, React (Vite) frontend.

**Live:** https://data-catalogue.somto.workers.dev

## Run locally

Requires Python 3.12+ with [uv](https://docs.astral.sh/uv/), and Node 22+.

```bash
# Terminal 1: API on http://127.0.0.1:8000
cd backend
uv run uvicorn app.main:app --app-dir src --reload

# Terminal 2: UI on http://localhost:5173
cd frontend
npm install
npm run dev
```

Locally the catalogue uses an in-memory store seeded with the three sample datasets, and a keyword-based
curator that needs no API key. The Vite dev server forwards `/datasets` to the API, so no CORS setup is needed.

## Test

```bash
cd backend && uv run pytest
cd frontend && npm test
```

## API

| Method | Path | Success | Errors |
| --- | --- | --- | --- |
| `GET` | `/datasets` | `200` list of datasets | |
| `POST` | `/datasets` | `201` saved dataset with `tags` and `summary` | `400` if `name` or `description` is missing or blank |
| `DELETE` | `/datasets/{id}` | `200` deleted dataset | `404` if the id does not exist |

Errors use one shape: `{"detail": "name is required"}`.

A dataset has `id`, `name`, `owner`, `description`, `tags`, `summary`, and `curation_status` (`"ok"` or `"failed"`).

## Structure

```
backend/
  src/app/
    main.py                 app setup, 400 validation handler, local wiring
    schemas.py              request and response models
    routers/datasets.py     HTTP layer: routes, status codes
    services/               business logic: create with curation, delete
    repositories/           DatasetStore protocol, in-memory store, D1 store, seed data
    curation/               Curator protocol, keyword curator, Workers AI curator
    cloudflare.py           Python/JavaScript value conversion for Cloudflare bindings
  src/worker.py             Cloudflare Worker entry: binds D1 and Workers AI to the app
  migrations/               D1 schema and seed rows
  wrangler.jsonc            Worker, D1, Workers AI, and static asset config
frontend/src/
  services/datasetsApi.ts   all HTTP calls and error parsing
  hooks/useDatasets.ts      list state: load, add, remove
  components/               DatasetForm, TextField, DatasetList, DatasetRow
  App.tsx                   page layout
```

## Deployment

One Cloudflare Worker serves both the API and the built frontend from the same origin.
The Python Worker handles `/datasets`; every other path is served from `frontend/dist` as static assets.
Storage is a D1 (SQLite) database and curation calls Workers AI, both through bindings, so no API keys are needed.

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
  default, so one handler changes this to `400` with a readable message.
- **Curation failure.** The service catches any curation error (network, timeout, invalid model output) and
  logs it. The dataset still saves with empty `tags` and `summary` and `curation_status: "failed"`. The UI
  shows this on the form and on the row.
- **LLM output.** The Workers AI request uses JSON mode with the `CurationResult` schema, and the reply is
  validated against the same schema. The prompt asks for 3–6 tags in fixed categories, one sentence of at
  most 25 words, and gives one worked example.
- **Keyword mock.** A table maps keywords to domain tags. PII is added for personal identifiers, or for a
  `name` field in a dataset about people, so "product name" does not count. Cadence comes from words like
  "daily". The summary is built from the field list in the description's first sentence.
- **Frontend state.** `useDatasets` loads the list once and updates it in place after add and delete, so
  the page does not reload. Components never call `fetch` directly.
