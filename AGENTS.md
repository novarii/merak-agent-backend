# Repository Guidelines

## Project Structure & Module Organization
Place the FastAPI application under `app/`; expose the ASGI entrypoint in `app/main.py` and group routers inside `app/api/`. Shared Pydantic models belong in `app/schemas/`, orchestrations and tool wiring in `app/services/`, and integrations with OpenAI vector stores or ChatKit in `app/integrations/`. Keep agent prompt templates and evaluation scripts in `agents/`. Store reference payloads or exploratory notebooks in `assets/` or `notebooks/` rather than alongside runtime modules. You MUST refer to `example_implementation.xml` when example is mentioned in integration plans.

## Build, Test, and Development Commands
- `python -m venv .venv && source .venv/bin/activate`: create and activate a local virtual environment.
- `pip install -r requirements.txt`: install runtime and tooling dependencies.
- `uvicorn app.main:app --reload`: run the FastAPI server with live reload for local development.
- `pytest`: execute the full test suite; use `pytest tests/api -k ranking` for targeted runs.
- `ruff check app tests` and `black app tests`: lint and format code before committing.

## Coding Style & Naming Conventions
Adopt Black’s defaults (4-space indentation, 88-character lines) and keep imports sorted via Ruff. Modules and packages use snake_case (`app/services/candidate_ranker.py`); classes stay in PascalCase, while functions, async endpoints, and fixtures remain snake_case. Preference async FastAPI route handlers and type hints for request/response bodies, tool payloads, and OpenAI client wrappers. Co-locate configuration constants in `app/core/settings.py`, keeping environment lookups centralized.

## Testing Guidelines
Write tests with Pytest. Place unit tests next to their modules (`tests/services/test_candidate_ranker.py`) and broader flows in `tests/integration/`. Name tests after behavior (`def test_ranker_handles_sparse_skills(...)`). Use fixtures for OpenAI and vector-store clients to avoid hitting remote services; provide lightweight stubs in `tests/fixtures/`. Maintain ≥85% coverage on touched modules and add regression cases whenever fixing defects.

## Commit & Pull Request Guidelines
Follow Conventional Commits (`feat(api): add contractor shortlisting`) with 72-character subject lines and explanatory bodies when needed. Reference issue IDs in the footer (`Refs #123`). Each pull request should describe the change, list validation commands, and include screenshots or cURL snippets for API-facing updates. Request reviews before merging, ensure CI is green, and tag the release captain on changes that touch production deployment paths.

## Security & Configuration Tips
Never commit secrets; load environment variables from `.env` and update `.env.example` when adding settings like `OPENAI_API_KEY` or vector index IDs. Validate configuration through `app/core/settings.py` so missing or malformed values fail fast. Rotate credentials used in fixtures and keep mock data devoid of PII. For external callbacks, document expected webhook URLs in `docs/architecture.md` and gate them behind authenticated endpoints.
