# E.D.E.N. Architecture Plan

E.D.E.N. (Evolving Dataset Evaluation Engine) is a backend-first AI infrastructure project for iteratively improving prompt datasets through a reproducible pipeline:

`generate -> clean -> score -> evaluate -> improve -> track -> repeat`

## Design Principles

- Modular services with clear ownership per lifecycle stage
- Transparent heuristics instead of opaque benchmark claims
- SQLite-backed experiment history for local reproducibility
- Backend abstractions that support local and hosted model backends
- Typed code, tests, documentation, and exported artifacts for reproducibility

## Core Components

1. `generators/`
   Template-driven and optionally LLM-assisted dataset generation.
2. `services/cleaning_service.py`
   Normalization, exact deduplication, semantic near-deduplication, and low-information filtering.
3. `scoring/`
   Prompt quality heuristics, semantic novelty, category-fit rules, and dataset-level score aggregation.
4. `evaluators/`
   Common evaluator interface with `mock`, `ollama`, `openai`, and `huggingface` backends.
5. `improvement/`
   Weak-prompt analysis, deterministic rewriting, rescoring, and version history tracking.
6. `monitoring/`
   Metric aggregation, trend snapshots, and chart-ready outputs.
7. `api/routes/`
   FastAPI routes exposing the full lifecycle.
8. `db/` and `models/`
   SQLAlchemy persistence for datasets, prompt items, scores, evaluation runs, outputs, improvements, and metric snapshots.

## Persistence Strategy

- SQLite is the default database for local experimentation.
- Dataset artifacts are also exported to `data/generated`, `data/cleaned`, and `data/scored` for easy inspection and demos.
- Evaluation summaries and charts are emitted under `evaluation/`.

## Phase Plan

### Phase 1
- Scaffold folders
- Create dependency and environment manifests
- Add minimal runnable FastAPI app

### Phase 2
- Add settings, logging, database setup, ORM models, and Pydantic schemas

### Phase 3
- Implement dataset generation, cleaning, semantic deduplication, and quality scoring

### Phase 4
- Implement model wrappers, evaluation heuristics, and the self-improvement loop

### Phase 5
- Wire FastAPI routes, metrics aggregation, artifact export, and demo pipeline scripts

### Phase 6
- Add tests, sample outputs, and README documentation

## Expected API Surface

- `POST /generate-dataset`
- `POST /clean`
- `POST /score`
- `POST /evaluate`
- `POST /improve`
- `GET /metrics`
- `GET /datasets`
- `GET /datasets/{dataset_id}`
- `GET /runs`
- `GET /health`
