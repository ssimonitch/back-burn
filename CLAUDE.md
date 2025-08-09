# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Development Commands

This project uses `poethepoet` (poe) as a task runner. All commands should be run with `uv run poe`:

### Core Development Commands
- `uv run poe dev` - Run the FastAPI development server with hot reload
- `uv run poe run` - Run the FastAPI production server

### Code Quality Commands
- `uv run poe format` - Format code using Black
- `uv run poe format-check` - Check code formatting without making changes
- `uv run poe lint` - Run Ruff linter to check for issues
- `uv run poe lint-fix` - Run Ruff linter and automatically fix issues
- `uv run poe typecheck` - Run MyPy type checking

### Testing Commands
- `uv run poe test` - Run all tests with pytest
- `uv run poe test-cov` - Run tests with coverage report
- `uv run poe test-verbose` - Run tests with verbose output
- Run a single test: `pytest tests/test_main.py::test_root_endpoint`

### Combined Commands
- `uv run poe check` - Run lint, typecheck, and format-check (use before committing)
- `uv run poe fix` - Run format and lint-fix to auto-fix issues
- `uv run poe ci` - Run full CI suite: lint, typecheck, format-check, and test-cov

## Architecture Overview

This is the backend for "Slow Burn", an AI Fitness Companion application built with FastAPI.

### Project Structure
```
backend/
├── main.py                 # FastAPI application entry point
├── src/                    # Source code directory
│   ├── api/               # API endpoints and routing
│   │   └── endpoints/     # Individual endpoint modules
│   ├── core/              # Core configuration and dependencies
│   ├── models/            # Pydantic models for validation
│   ├── repositories/      # Thin repository layer (Supabase-backed implementations)
│   ├── services/          # Business logic and external integrations
│   └── utils/             # Utility functions
├── tests/                  # Test files
└── docs/                   # Project documentation
    └── planning/          # Sprint planning and tracking
```

### Key Technologies
- **Framework**: FastAPI (async Python web framework)
- **Python Version**: 3.12+
- **Package Manager**: uv
- **Database**: PostgreSQL (via Supabase)
- **AI Service**: Google Gemini 2.5 Flash API
- **Vector Search**: pgvector extension for semantic memory

## Project Documentation

### Project Brief
The complete project vision and technical details are documented in `docs/00_project_brief.md`. This includes:
- Backend vision and core responsibilities
- Complete technology stack details
- High-level architecture overview
- 8-week MVP sprint timeline with backend-specific tasks

### Sprint Planning & Tracking
The project uses structured sprint planning located in `docs/planning/`:
- `sprint_summary.md` - Overall project status and sprint overview
- `dependencies_map.md` - Task dependencies and critical path analysis
- `sprints/` directory - Individual sprint task boards and progress tracking

Current sprint information:
- **Sprint 1**: ✅ Foundation & Setup (Complete)
- **Sprint 2**: ✅ Authentication & Database Schema (Complete)
  - ✅ Database schema fully implemented with production-ready features
  - ✅ JWT authentication flow fully implemented with JWKS validation
  - ✅ Protected endpoints created with comprehensive test coverage
  - ✅ Database relationships documented in docs/01_database.md
- **Sprint 3**: 🏃 Plan Creation (60% Complete - February 5, 2025)
  - ✅ All Plan CRUD endpoints implemented (POST, GET, GET by ID, PUT, DELETE)
  - ✅ Pydantic models created with modern best practices (40% code reduction)
  - ✅ Full authentication and validation on all endpoints
  - ✅ Versioning support implemented for plan updates
  - ✅ Comprehensive test suite (26 tests, 70% coverage)
  - 📅 Service layer and documentation tasks remaining

## Important Context

### Authentication Flow (Sprint 2 - Completed)
- Frontend handles authentication directly with Supabase
- Backend receives JWT tokens in Authorization header
- Backend validates JWTs using JWKS public key verification (src/core/auth.py)
- Automatic key rotation handling with 10-minute cache TTL
- Fallback to Supabase API validation for reliability
- All protected endpoints use require_auth dependency
- Optional authentication available with optional_auth dependency
- UserContext model provides typed access to authenticated user data

### AI Integration Architecture
When implementing chat endpoints:
1. Receive user message
2. Query memories table using pgvector for relevant context
3. Construct prompt with AI persona + retrieved memories + user message
4. Send to Google Gemini API
5. Process structured JSON response
6. Update affinity score if applicable
7. Return response to frontend

## Working with the Repository Pattern

- Endpoints depend on repository protocols via DI. Provider: `src/core/di.py` (`get_plans_repository`).
- Repositories are intentionally thin and return raw dicts. Endpoints construct/validate Pydantic models to keep API contract enforcement centralized.
- Keep repository APIs minimal. Add methods only when they reduce duplication in endpoints and tests (e.g., `list`, `get_raw`, `insert_plan`, `mark_inactive`, `soft_delete_cascade`).

### Tests
- Prefer mocking repositories over Supabase chains: use `mock_plans_repo` fixture from `tests/conftest.py`.
- Example:
```python
def test_list_plans(mock_auth_dependency, mock_plans_repo):
    mock_plans_repo.list.return_value = ([{"id": "...", "name": "..."}], 1)
    # call endpoint and assert
```

### OpenAPI Contract
- Keep endpoints model-first. When repositories change, the OpenAPI schema should not drift because models and routes remain the single source of truth.

### Database Schema (Sprint 2 - Completed)
All core tables have been implemented with production-ready features:

#### Core Tables:
- **Users**: Profile data with affinity_score, preferences (JSONB), fitness level
- **Plans**: Workout plan templates with versioning system and public/private sharing
- **Exercises**: Comprehensive exercise library with biomechanical classification
- **Workout_sessions**: Actual workout instances with RPE and wellness tracking
- **Sets**: Detailed performance logs with volume calculations, tempo, RIR, and form quality
- **Memories**: AI conversation history with halfvec(3072) embeddings for semantic search
- **Conversations**: Chat session management for AI interactions

#### Supporting Tables:
- **Reference tables**: movement_patterns, muscle_groups, equipment_types, training_styles
- **Junction tables**: exercise_movement_patterns, exercise_muscles, exercise_training_styles
- **Relationships**: exercise_relationships for variations and progressions

#### Key Features Implemented:
- pgvector with HNSW indexing for fast similarity search
- Row-level security (RLS) policies on all tables
- Foreign key indexes for performance optimization
- Database functions: search_memories(), increment_affinity_score()
- Automatic updated_at triggers where applicable

### Database Considerations
- Never expose database credentials to frontend
- Use row-level security (RLS) in Supabase
- Vector embeddings stored in memories table for semantic search
- Affinity score tracked in Users table

### Security Requirements
- All sensitive credentials must be in environment variables
- Never commit secrets to the repository
- Validate all incoming data with Pydantic models
- Implement proper CORS policies before deployment

## Pydantic Best Practices

### Type Safety with Enums
- Use `StrEnum` (Python 3.11+) for categorical fields instead of plain strings
- Define enums in `src/models/enums.py` for reusability across models
- Benefits: Type safety, IDE autocomplete, automatic API documentation

Example:
```python
from enum import StrEnum

class TrainingStyle(StrEnum):
    POWERLIFTING = "powerlifting"
    BODYBUILDING = "bodybuilding"
```

### Field Validation
- Use Pydantic's built-in field constraints over custom validators when possible
- Prefer `Field(min_length=1, max_length=100)` over `constr()` annotations
- Use `Field(gt=0, le=52)` for numeric constraints instead of `conint()`
- Only write custom validators for complex business logic

### Model Configuration
- Use `use_enum_values=True` for automatic enum serialization
- Enable `str_strip_whitespace=True` for automatic string cleaning
- Set `extra="forbid"` to catch typos and unexpected fields early
- Use `validate_assignment=True` for runtime validation of field updates

### Field Documentation
- Only add descriptions for complex fields that need explanation
- Remove redundant descriptions for self-explanatory fields (id, name, created_at)
- Keep descriptions for business-critical fields (metadata, version_number)

## Supabase Local Development

### Setup and Commands:
- `supabase start` - Start local Supabase stack (PostgreSQL, Auth, etc.)
- `supabase stop` - Stop local Supabase stack
- `supabase db reset` - Reset database and rerun all migrations
- `supabase migration new <description>` - Create a new migration file
- `supabase db diff -f <description>` - Generate migration from database changes (optional)
- `supabase migration list` - View all migrations and their status

### Database Migration Workflow:
The project uses **imperative migrations** for simplicity and straightforward AI collaboration.

#### Migration Management:
- `supabase migration new <description>` - Create a new migration file
- `supabase db diff -f <description>` - Generate migration from database changes (when needed)
- All database changes go in timestamped migration files in `supabase/migrations/`

#### Development Workflow:
1. **Making Schema Changes**:
   ```bash
   # Create a new migration
   supabase migration new add_user_timezone

   # Edit the generated migration file with your SQL changes
   # Example: supabase/migrations/20250804123456_add_user_timezone.sql

   # Test locally
   supabase db reset

   # Commit the migration file
   ```

2. **Migration Best Practices**:
   - Use descriptive names: `add_user_preferences`, `update_plans_schema`, `fix_rls_policies`
   - Keep migrations focused on single logical changes
   - Include both schema changes and RLS policies in the same migration
   - Test all migrations with `supabase db reset` before committing
   - Write reversible migrations when possible (include DROP statements in comments)

3. **Benefits of Imperative Approach**:
   - Simple, linear migration history
   - RLS policies and schema changes in same files
   - No conflicts with `supabase db diff`
   - AI-friendly workflow
   - Standard PostgreSQL migration pattern

## Development Workflow

1. Always run `uv run poe check` before committing code
2. Fix any issues with `uv run poe fix`
3. Write tests for new functionality
4. Follow existing code patterns and conventions
5. Use `@agent-sprint-manager` to update sprint documentation in docs/planning/ as tasks are completed
6. When working with database:
   - Test migrations locally with `supabase db reset`
   - Check Supabase Dashboard for any performance/security warnings
   - Ensure RLS policies are properly enabled on new tables
