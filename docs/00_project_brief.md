# **Backend Development Overview: AI Fitness Companion**

This document outlines the vision, architecture, and development plan for the backend portion of Slow Burn, an AI Fitness Companion application. It serves as the primary guide for all backend-related tasks during the MVP development cycle.

## **1\. Backend Vision & Core Responsibilities**

The backend is the engine of the application, responsible for all business logic, data persistence, and secure communication with third-party services. Its primary goal is to provide a fast, secure, and reliable API for the frontend, while also orchestrating the complex interactions required to bring the AI companion to life.

**Key Responsibilities:**

* Implement a secure RESTful API to handle all CRUD (Create, Read, Update, Delete) operations for fitness data (users, plans, workouts, etc.).
* Serve as a secure gateway to the Supabase database, never exposing database credentials directly to the client.
* Manage all interactions with the Google Gemini API, including prompt construction, semantic memory retrieval, and response handling.
* Implement the core business logic for the affinity system, calculating and updating the user's score based on their actions.
* Enforce data validation and integrity for all incoming requests.

## **2\. Technology Stack & Tooling**

Our backend stack is chosen for performance, scalability, and its first-class AI/ML ecosystem.

* **Framework:** **FastAPI** (for its high performance and automatic data validation)
* **Language:** **Python 3.12+**
* **Package Manager/Virtual Env:** **uv** (for its speed and modern dependency resolution)
* **Linting/Formatting:** **Ruff** (as an all-in-one, high-speed linter and formatter)
* **Data Validation:** **Pydantic** (integrated natively into FastAPI)
* **Database:** **PostgreSQL** (managed via Supabase)
* **AI Service:** **Google Gemini 2.5 Flash API**

## **3\. High-Level Backend Architecture**

The backend will be a stateless API service that follows RESTful principles.

* **API Structure:** Endpoints will be organized logically using FastAPI's APIRouter. For example, all endpoints related to workout plans will be grouped under a /plans router.
* **Data Validation:** Pydantic models will be used extensively to define the expected request and response shapes for all API endpoints. This provides automatic request validation and clear, auto-generated API documentation (via Swagger UI and ReDoc).
* **API Contract & Workflow:** The OpenAPI schema (`openapi.json`) is the single source of truth for the API. The backend generates it from FastAPI, validates it in CI, and the frontend consumes it for types and client generation.
* **Authentication Flow (Hybrid Model):**
  * **Frontend Responsibility:** The React frontend handles all primary user-facing authentication actions (Sign Up, Login, Password Reset, etc.) by interacting directly with the Supabase client-side library (supabase-js).
  * **Backend Responsibility:** The backend does not have user-facing endpoints like `/login` or `/signup`. Its sole authentication duty is to act as a protected resource server. On every incoming request to a protected endpoint, a FastAPI dependency will validate the JWT sent in the `Authorization` header. This validation is done locally and performantly using a cached JWKS.
  * **Server-Side Actions:** The `supabase-py` library will be used on the backend only for infrequent, server-initiated auth actions if needed in the future (e.g., admin tasks), not for handling user sessions.
* **Database Interaction:** All database operations will be handled through the `supabase-py` client library or a direct PostgreSQL connector like psycopg2. The backend will contain all the SQL queries or ORM logic, abstracting the database layer from the frontend.
* **Repository Pattern & DI:** A thin repository layer abstracts data-access (e.g., `PlansRepository`). Repositories are provided via FastAPI DI (see `src/core/di.py`). Repositories return raw dicts; endpoints construct Pydantic models and map validation errors to HTTP responses to keep the API contract centralized and stable.
  * Typing: Repository outputs use minimal `TypedDict`s (e.g., `DBPlanRow`) to improve editor/type safety without coupling endpoints to schema internals.
  * Testing & Coverage: The test suite enforces a minimum 80% coverage threshold to prevent regressions.
* **AI Interaction Flow:** For a chat request, the backend will:
  1. Receive the user's message from the frontend.
  2. Use the user's user\_id to query the memories table in PostgreSQL, performing a vector similarity search with pgvector to find relevant past interactions.
  3. Construct a detailed system prompt containing the AI's persona, the retrieved memories, and the user's new message.
  4. Send the complete prompt to the Google Gemini API.
  5. Receive the structured JSON response from Gemini.
  6. Perform any necessary business logic (e.g., logging the interaction).
  7. Return the final JSON payload to the frontend.

### API Contract Details

- **Generation & Verification**
  - Generate schema: `uv run poe generate-openapi`
  - Verify schema: `uv run poe verify-openapi` (validates if validator is installed)
  - Publish to frontend: `uv run poe publish-openapi`

- **Versioning Source**
  - API version is read from `pyproject.toml` and embedded in the schema `info.version`.
  - SemVer policy:
    - Patch: strictly additive, non-breaking (docs/example updates)
    - Minor: backward compatible additions (new endpoints/fields)
    - Major: breaking changes (field removal/rename, type changes, auth changes)

- **Auth Model**
  - Global Bearer auth is required unless an operation explicitly sets `security: []`.
  - Public routes: `/`, `/health`, `/api/v1/auth/public`.

- **Pagination Contract**
  - Response body includes: `items`, `total`, `page`, `per_page`.
  - No `X-Total-Count` header; `has_next` can be computed by clients.

### Breaking Change Policy

- What is breaking:
  - Removing or renaming fields, changing field types or requiredness
  - Changing auth requirements for existing operations
  - Path changes or response envelope changes

- Required actions:
  - Bump major version in `pyproject.toml` (propagates to schema)
  - Communicate impact to frontend and coordinate rollout
  - Consider deprecation periods and dual-contract windows where feasible

### Testing Alignment

- Tests should reflect OpenAPI shapes. Pydantic models enforce schema alignment.
- Avoid undocumented fields in examples. If the schema changes, update tests and `openapi.json` together.

## **4\. Backend MVP Sprint Plan (8 Weeks)**

This timeline details the backend-specific goals and tasks for each sprint of the MVP development.

| Sprint | Goal                                       | Backend-Specific Tasks                                                                                                                                                                                                              |
| :----- | :----------------------------------------- | :---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **1**  | **Foundation & Setup**                     | Initialize the FastAPI project using uv. Set up Ruff for linting/formatting and configure pre-commit hooks. Create the basic project structure. Set up the Render project and confirm initial "Hello World" deployment.             |
| **2**  | **Authentication & Database Schema**       | Implement the database schema in Supabase (Users, Plans, Exercises, Sets, Memories with vector column). Create a secure dependency in FastAPI to validate Supabase JWTs from incoming requests.                                     |
| **3**  | **Plan Creation**                          | Develop the API endpoints for creating (POST /plans), reading (GET /plans), updating (PUT /plans/{plan\_id}), and deleting (DELETE /plans/{plan\_id}) workout plans. Implement the database logic for these operations.             |
| **4**  | **Workout Logging**                        | Create the API endpoint (POST /workouts/log) to receive and persist a completed workout session from the frontend. Implement the logic to save all associated sets, reps, and weights to the database.                              |
| **5**  | **Exercise Library**                       | Create the API endpoint (GET /exercises) to fetch and return the list of available exercises from the database. Implement logic for searching or filtering exercises if needed.                                                     |
| **6**  | **AI \- Chat Interface & Semantic Memory** | Create the /chat endpoint. Implement the logic to: 1\) receive a message, 2\) convert it to an embedding, 3\) query pgvector for relevant memories, 4\) construct a prompt, 5\) call the Gemini API, and 6\) return the response.   |
| **7**  | **AI \- Affinity System**                  | Implement the business logic for the affinity system. Modify the /workouts/log endpoint to increment the user's affinity\_score in the Users table upon successful completion. Pass the affinity\_score into the AI prompt context. |
| **8**  | **Final Testing & Security**               | Conduct end-to-end testing of all API endpoints. Review security best practices (e.g., environment variable management, CORS policies). Ensure all configurations for deployment on Render are finalized.                           |
