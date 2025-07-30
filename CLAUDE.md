# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Development Commands

This project uses `poethepoet` (poe) as a task runner. All commands should be run with `poe`:

### Core Development Commands
- `poe dev` - Run the FastAPI development server with hot reload
- `poe run` - Run the FastAPI production server

### Code Quality Commands
- `poe format` - Format code using Black
- `poe format-check` - Check code formatting without making changes
- `poe lint` - Run Ruff linter to check for issues
- `poe lint-fix` - Run Ruff linter and automatically fix issues
- `poe typecheck` - Run MyPy type checking

### Testing Commands
- `poe test` - Run all tests with pytest
- `poe test-cov` - Run tests with coverage report
- `poe test-verbose` - Run tests with verbose output
- Run a single test: `pytest tests/test_main.py::test_root_endpoint`

### Combined Commands
- `poe check` - Run lint, typecheck, and format-check (use before committing)
- `poe fix` - Run format and lint-fix to auto-fix issues
- `poe ci` - Run full CI suite: lint, typecheck, format-check, and test-cov

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
- **Sprint 2**: 🏃 Authentication & Database Schema (60% Complete)
  - ✅ Database schema fully implemented with production-ready features
  - 🏃 Currently working on: JWT validation flow design
  - Next: JWT implementation and protected endpoints

## Important Context

### Authentication Flow
- Frontend handles authentication directly with Supabase
- Backend receives JWT tokens in Authorization header
- Backend validates JWTs with Supabase to extract user_id
- All protected endpoints require valid JWT

### AI Integration Architecture
When implementing chat endpoints:
1. Receive user message
2. Query memories table using pgvector for relevant context
3. Construct prompt with AI persona + retrieved memories + user message
4. Send to Google Gemini API
5. Process structured JSON response
6. Update affinity score if applicable
7. Return response to frontend

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

## Supabase Local Development

### Setup and Commands:
- `supabase start` - Start local Supabase stack (PostgreSQL, Auth, etc.)
- `supabase stop` - Stop local Supabase stack
- `supabase db reset` - Reset database and rerun all migrations
- `supabase migration new <name>` - Create new migration file
- `supabase migration list` - View all migrations and their status

### Migration Files:
All database migrations are in `supabase/migrations/`:
- Migrations run in alphabetical order by timestamp
- Each migration should be idempotent when possible
- RLS policies and indexes are in separate migration files for clarity

## Development Workflow

1. Always run `poe check` before committing code
2. Fix any issues with `poe fix`
3. Write tests for new functionality
4. Follow existing code patterns and conventions
5. Update sprint documentation in docs/planning/ as tasks are completed
6. When working with database:
   - Test migrations locally with `supabase db reset`
   - Check Supabase Dashboard for any performance/security warnings
   - Ensure RLS policies are properly enabled on new tables