## Slow Burn Backend (AI Fitness Companion)

The Slow Burn backend is a FastAPI service that powers an AI fitness companion. It provides secure, high‑performance REST endpoints for authentication, workout plans, workout logging (upcoming), and AI features (Gemini) while enforcing strict validation and data integrity.

### Tech Stack
- **Framework**: FastAPI (Python 3.12)
- **Data & Auth**: Supabase (Postgres + RLS)
- **Validation**: Pydantic
- **AI**: Google Gemini (planned)
- **Tooling**: uv, poe the poet, Ruff, Black, MyPy, Pytest

### Project Links
- API docs (local): `/docs` and `/redoc`
- OpenAPI schema: `openapi.json` at the repo root
- Extended docs: `docs/`
  - Project brief: `docs/00_project_brief.md`
  - Database: `docs/01_database.md`
  - API reference (plans): `docs/02_api_documentation.md`

## Getting Started

### Prerequisites
- Python 3.12+
- `uv` installed (`pipx install uv`)

### Install dependencies
```bash
uv sync
```

### Run the API locally
```bash
# Live-reload dev server
uv run poe dev

# Or run without live-reload
uv run poe run
```

### Environment
Configuration is loaded from the `.env.*` chain by `src/core/settings.py`.
Key settings include API host/port, frontend CORS origin, and Supabase keys.

## Development Commands (poe)

### Code quality
```bash
uv run poe format         # Format code with Black
uv run poe format-check   # Check formatting only
uv run poe lint           # Lint with Ruff
uv run poe lint-fix       # Lint + auto-fix
uv run poe typecheck      # MyPy type checking
```

### Tests
```bash
uv run poe test           # Run tests
uv run poe test-cov       # Tests with coverage
uv run poe test-verbose   # Verbose test output
```

Coverage gate: tests must maintain >= 80% coverage (enforced via pytest config).

### Combined flows
```bash
uv run poe check          # Lint + typecheck + format-check
uv run poe fix            # Format + lint-fix
uv run poe ci             # CI pipeline (lint, typecheck, format-check, test-cov, verify-openapi)
```

## OpenAPI Workflow

The OpenAPI schema is the source of truth for the frontend API contract. It includes global bearer auth, explicit public endpoints, and a `servers` block for local tooling.

```bash
uv run poe generate-openapi   # Generate openapi.json (deterministic output)
uv run poe verify-openapi     # Verify openapi.json matches current app
uv run poe publish-openapi    # Copy schema to ../frontend/openapi.json (generates if missing)
```

Options and tips:
- `uv run python scripts/verify_openapi.py --update` auto‑regenerates on mismatch (useful locally).
- The schema is validated (if `openapi-spec-validator` is installed). Skip via `--no-validate`.
- Frontend can generate types and clients from `openapi.json`.

## API Overview

Current implemented areas include authentication and workout plans with immutable versioning. See `docs/02_api_documentation.md` for endpoint details, payloads, and examples.

Pagination for list endpoints returns a body of `{ items, total, page, per_page }`.

## Directory Highlights
- `main.py`: FastAPI app, CORS, OpenAPI customization (servers, global security, public routes)
- `src/`: Application code (auth, models, routers, utilities)
- `src/repositories/`: Thin data-access layer (Repository pattern)
- `scripts/`: Development scripts
  - `generate_openapi.py`: Emit `openapi.json`
  - `verify_openapi.py`: Check for schema drift, optional validation and `--update`
  - `publish_openapi.py`: Copy schema to frontend
- `tests/`: Test suite
- `docs/`: Architecture, database, and API documentation

## Troubleshooting
- Import errors running scripts: run from the backend directory and ensure dependencies are installed (`uv sync`).
- Schema drift in CI: run `uv run poe generate-openapi` and commit the updated `openapi.json`.
- CORS issues: adjust `frontend_url` in environment to match your frontend origin.

---

For deeper context on architecture and sprints, see `docs/00_project_brief.md` and `docs/01_database.md`. For API usage examples, see `docs/02_api_documentation.md` and the generated Swagger docs at `/docs`.

### Repository Pattern & DI

We use a thin Repository pattern to abstract Supabase calls and make tests stable and concise.

- **Protocol**: See `src/repositories/plans.py` for `PlansRepository` interface and `SupabasePlansRepository` implementation.
- **Dependency Injection**: Endpoints depend on repositories via FastAPI DI. Provider lives in `src/core/di.py` as `get_plans_repository`.
- **Model-first endpoints**: Repositories return raw dicts; endpoints construct Pydantic models and map `ValueError`/`ValidationError` to HTTP errors to preserve API behavior and OpenAPI contracts.
- **Lightweight typing**: Repository outputs use minimal `TypedDict`s for DB rows (e.g., `DBPlanRow`) to improve editor/type safety without coupling endpoints to SQL schemas.

Testing with the Repository pattern:

```python
# Example (pytest): override repo in tests
from fastapi.testclient import TestClient
from main import app
from src.core.di import get_plans_repository

def test_example(mock_auth_dependency):
    mock_repo = __import__("unittest.mock").mock.MagicMock()
    mock_repo.list.return_value = ([], 0)
    app.dependency_overrides[get_plans_repository] = lambda: mock_repo

    client = TestClient(app)
    res = client.get("/api/v1/plans/", headers={"Authorization": "Bearer t"})
    assert res.status_code == 200

    app.dependency_overrides.pop(get_plans_repository, None)
```

Prefer using the shared `mock_plans_repo` fixture from `tests/conftest.py` which handles overrides automatically.
