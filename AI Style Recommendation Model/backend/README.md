# Style recommendation backend

FastAPI backend for catalog filtering, preference extraction, ranking, and visual styling advice. The frontend continues to use `/fashion-recommendation/api/*`.

## Run

From this directory, using the same Python interpreter that will serve requests:

```powershell
python -m pip install -e "."
python -m uvicorn style_recommendation.main:app --reload
```

The legacy command `python -m uvicorn app.main:app --reload` still works. Standalone execution serves `/api/*`, `/images/*`, and `/fashion-recommendation/*` aliases. The unified gateway in `../../server/server.py` still mounts the backend under `/fashion-recommendation` and `/styleanalyzer` and explicitly owns its lifecycle. No frontend changes are required.

The gateway first imports the installed `style_recommendation` package. A source-checkout fallback supports the existing gateway launch command without an editable install. If using `server/venv`, install this backend into that interpreter:

```powershell
& "../../server/venv/Scripts/python.exe" -m pip install -e "."
```

Existing gateway and backend dependency pins differ; use the serving environment's dependency policy when installing, rather than replacing its packages blindly. For an environment that already has the backend dependencies, `pip install --no-deps -e "."` only registers the package.

The schema layer supports the gateway's Pydantic 1 and standalone Pydantic 2 environments. No gateway dependency upgrade is required. To check imports, validation, extraction, export, and API contracts in the actual serving interpreter without contacting the models, run:

```powershell
& "../../server/venv/Scripts/python.exe" tests/serving_smoke.py
```

## Structure

```text
style_recommendation/
  main.py          # Application factory, error handlers, route registration
  core/            # Settings, resource composition, lifecycle, logging, paths
  api/routes/      # Thin HTTP handlers
  api/dependencies.py
  schemas/         # Request validation and response contracts
  services/        # Requirement, recommendation, and stylist workflows
  inference/       # Qwen, FashionCLIP worker, Cartographer adapters
  repositories/    # Catalog loading/normalization and JSON exports
  prompts/         # Packaged prompt resources
app/main.py        # Legacy entry point
scripts/           # Explicit maintenance commands
tests/unit/        # Matching, scoring, inference adapters, evidence, progress
tests/integration/ # API contracts, workflows, lifecycle, storage, packaging
```

`create_app(settings=None, resources=None)` creates an independent dependency graph. Tests can supply resources or override functions from `api/dependencies.py`. Production services receive collaborators through constructors and never import service singletons.

The recommendation workflow extracts preferences, filters the catalog, ranks candidates, keeps exact matches separate from alternatives, and optionally exports the result. Existing eligibility, shade handling, score weights, and visual-to-text-to-metadata fallback rules are preserved. Export failures are logged and do not discard recommendations.

## Configuration and model artifacts

Copy `.env.example` to `.env` and set the values needed locally. Existing environment variables take precedence over `backend/.env`, then the parent model project's `.env`. Relative data, model, result, and cache paths resolve against `STYLE_BASE_DIR`; they do not depend on the process working directory. Its source-checkout default is the `AI Style Recommendation Model` directory. Set `STYLE_BASE_DIR` explicitly for a wheel installed elsewhere.

| Variable | Default relative to model project |
| --- | --- |
| `DATASET_PATH` | `data/product_full_updated.csv` |
| `IMAGES_DIR` | `Images` |
| `OCCASION_MAPPING_PATH` | `config/occasion_mapping.json` |
| `RESULTS_DIR` | `results` |
| `ARTIFACTS_DIR` | `artifacts` |
| `RANKER_MODEL_PATH` | `artifacts/ranker` |
| `FASHIONCLIP_MODEL_PATH` | `artifacts/fashionclip` |
| `FASHIONCLIP_CACHE_DIR` | `.cache/fashionclip` |

Model names remain `qwen2.5:7b` for preferences and `qwen3-vl:8b` for styling, served by `OLLAMA_BASE_URL` (default `http://localhost:11434`). Existing ranker enablement, batching, timeout, and thread controls remain available; see `.env.example` and `RANKER.md`.

Local model trees now live outside Python source. For another checkout with the old layout, run these commands from the backend directory **before starting its server**, unless explicit model paths already point elsewhere:

```powershell
python -m scripts.migrate_artifacts app/RankerModel ../artifacts/ranker
python -m scripts.migrate_artifacts app/fashionclip ../artifacts/fashionclip
```

The migration preserves the complete directory, including ignored weight/ONNX files, and refuses to overwrite an existing destination. Keep source and destination on the same filesystem. This checkout's existing files have already been migrated. Large weights remain local and ignored by Git; provision them separately on a new machine. No model downloads occur automatically.

Startup loads and normalizes the catalog and checks Ollama; inference weights load lazily on first use. Shutdown closes the visual worker. `/api/health` reports degraded availability for a missing catalog, unavailable inference server, or failed ranker. Inspecting health never loads weights or retries the catalog. Place an optional `placeholder.jpg` in `IMAGES_DIR` for missing image fallback; application imports never copy assets from the frontend.

Requests strip surrounding whitespace and normalize sizes to uppercase. Invalid/blank inputs now return FastAPI validation errors with HTTP **422** (previous manual checks returned 400). Successful response fields and missing-product 404 responses are preserved.

## Verify

```powershell
python -m pytest tests -q --basetemp=.pytest-tmp-local
python -m compileall -q style_recommendation app scripts
```

Tests use injected inference substitutes and do not require Ollama or loaded model weights. They cover the original catalog scenarios, exact/alternative evidence, ranker fallbacks, API aliases, malformed model output, image containment, result storage, resource isolation, and mounted lifecycle cleanup. Actual model quality/latency still requires a local inference smoke test with provisioned artifacts and Ollama.

Maintenance commands use `python -m scripts.check_data --dataset PATH` or `python -m scripts.add_sizes --dataset PATH`. The latter modifies the selected catalog; it is not part of server startup or tests.
