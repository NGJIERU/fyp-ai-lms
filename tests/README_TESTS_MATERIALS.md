# Material Crawling & Repository Module Tests

This document describes the automated test coverage for the **Material Crawling & Repository** module.

## Test Files

- **`tests/test_material_models.py`**  
  Unit tests for:
  - `Material` model
  - `MaterialTopic` model
  - `CrawlLog` model

- **`tests/test_crawler_manager.py`**  
  Unit tests for:
  - `CrawlerManager` registration and retrieval
  - `run_crawler` workflow (happy path and error path)
  - Deduplication logic based on `url` and `content_hash`
  - Crawl logging via `CrawlLog` (status, items_fetched, errors)

- **`tests/test_materials_api.py`**  
  API integration tests for materials-related endpoints:
  - `GET /materials/` (listing + filtering)
  - `GET /materials/search` (simple text search)
  - `GET /materials/course/{course_id}/week/{week_number}` (course-week mappings)
  - `POST /materials/{material_id}/approve` (lecturer approval and mapping)

- **`tests/test_crawling_api.py`**  
  API integration tests for crawling trigger endpoint:
  - `POST /materials/crawl` (role-based access and validation)

## Coverage Summary

### Models

- **`Material`**
  - Creation with required fields
  - URL uniqueness constraint
  - `quality_score` range constraint `[0.0, 1.0]`
  - `generate_content_hash` determinism and length (64 hex characters)
  - Timestamps: `created_at`, `updated_at`

- **`MaterialTopic`**
  - Creation and relationships to `Material`, `Course`, and `User` (approver)
  - `week_number` constraint: `1–14`
  - `relevance_score` constraint: `0.0–1.0`
  - Cascade deletes when `Material` or `Course` is deleted

- **`CrawlLog`**
  - Creation defaults: `status="running"`, `items_fetched=0`, `started_at` set
  - Status transitions to `completed` with `items_fetched` and `finished_at`

### Services (CrawlerManager)

- Registration and retrieval of crawler instances
- `run_crawler` workflow:
  - Calls crawler `fetch` and `parse`
  - Normalizes data via crawler
  - Saves `Material` records using deduplication:
    - Skip if `url` already exists
    - Skip if `content_hash` already exists
  - Commits `CrawlLog` with:
    - `status="completed"` on success
    - `items_fetched` equal to saved materials
    - `finished_at` timestamp
- Error handling:
  - Exceptions during crawling update `CrawlLog` to `status="failed"`
  - Stores error message and stack trace

### API Endpoints

- **`GET /materials/`**
  - Pagination via `skip`, `limit`
  - Filtering by `type`, `source`, `min_quality`

- **`GET /materials/search`**
  - Simple ILIKE-based search on `title` and `description`
  - Returns `MaterialSearchResult` schema with mock similarity scores

- **`GET /materials/course/{course_id}/week/{week_number}`**
  - Returns `MaterialTopicRead` entries for a specific course week
  - Includes hydrated `material` object and `course_name`

- **`POST /materials/{material_id}/approve`**
  - Only lecturers (via `get_current_lecturer`) can approve/map
  - Creates new mapping when none exists
  - Updates existing mapping (relevance score and approval info) when duplicate
  - 404 when material does not exist
  - Students cannot approve (expected 401/403 depending on auth)

- **`POST /materials/crawl`**
  - Only `LECTURER` and `SUPER_ADMIN` roles can trigger crawling
  - Supports:
    - Specific `crawler_type`
    - `crawler_type=None` to run all registered crawlers
  - Validates `max_items` (>=1 and <=1000)
  - Returns `CrawlResponse` with:
    - `status="accepted"`
    - `crawler_type` (`specific` or `"all"`)
    - `items_fetched=0` (async execution)

## How to Run

From project root:

```bash
# Run only material module tests
pytest \
  tests/test_material_models.py \
  tests/test_crawler_manager.py \
  tests/test_materials_api.py \
  tests/test_crawling_api.py -v

# Run all tests (full backend suite)
pytest tests/ -v
```

For coverage reporting:

```bash
pytest tests/ --cov=app --cov-report=html
```

Then open `htmlcov/index.html` in a browser to inspect coverage, focusing on the
Material Crawling & Repository module files:

- `app/models/material.py`
- `app/services/crawler/manager.py`
- `app/api/v1/endpoints/materials.py`
