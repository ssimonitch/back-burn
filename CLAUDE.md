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
- **Sprint 2**: 🏃 Authentication & Database Schema (In Progress)
- Focus: Database schema design, JWT validation, and Supabase setup

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

### Database Schema (Sprint 2)
Core tables being implemented:
- **Users**: Profile data with affinity_score
- **Plans**: Workout plan templates
- **Exercises**: Exercise library with metadata
- **Sets**: Workout performance logs with relationships to Plans/Exercises
- **Memories**: AI conversation history with vector embeddings (pgvector)

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

## Development Workflow

1. Always run `poe check` before committing code
2. Fix any issues with `poe fix`
3. Write tests for new functionality
4. Follow existing code patterns and conventions
5. Update sprint documentation in docs/planning/ as tasks are completed