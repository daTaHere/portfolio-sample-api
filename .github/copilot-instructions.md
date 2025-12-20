# Repository Architecture & AI Instructions

## Architecture Overview

This is a **production-grade Flask API** using **layered, service-oriented architecture** with strict separation of concerns:

- **Routes** (`app/routes/`) - HTTP layer only, no business logic. Handle request/response, delegate to services
- **Services** (`app/services/`) - Business logic and orchestration. All async using `asyncio`/`httpx`
- **Models** (`app/models/`) - Domain models using `__slots__` for memory efficiency (not SQLAlchemy ORM)
- **DTOs** (`app/dto/`) - Internal data boundaries between layers (e.g., `FeedCache` for cache operations)
- **Schemas** (`app/schemas/`) - Marshmallow schemas for ALL input/output validation
- **Clients** (`app/clients/`) - External system adapters (Redis, third-party APIs)
- **Exceptions** (`app/exceptions/`) - Custom exception hierarchy with context (`APIException`, `ServiceException`, `DatabaseException`)

**Critical:** Routes call services, services orchestrate workflows, models are plain Python classes (NOT SQLAlchemy models for feeds/comments).

## Explicit Restrictions (DO NOT)

- Do NOT place business logic in routes — routes delegate only
- Do NOT bypass the service layer from routes or clients
- Do NOT introduce SQLAlchemy ORM models for feeds/comments
- Do NOT return raw dicts or lists from services (use models + schemas)
- Do NOT skip Marshmallow validation for any API response
- Do NOT cache raw external API responses (always use DTO + schema)
- Do NOT instantiate Flask directly — always use `create_app`
- Do NOT use `logger.*` directly — use `handle_log`


## Key Design Patterns

### 1. Application Factory Pattern
Use `create_app(config_name)` from `app/__init__.py`. Never instantiate Flask directly.
```python
from app import create_app
app = create_app('development')
```

### 2. Structured Logging
Use `handle_log()` helper from `app/utils/logger_helper.py` with standardized fields:
```python
handle_log(
    "Description of event",
    method="GET",
    event_key="SUCCESS",  # CACHE_HIT, ERROR, etc.
    log_level="info",      # debug, info, warning, error
    service_method="function_name",
    **extra_fields
)
```
For debug logging, use `debug_logger(name)` which returns a structlog-bound logger.

### 3. Exception Handling Pattern
- Services raise `APIException` (external API failures) or `ServiceException` (business logic errors)
- Routes catch these and use `handle_route_error()` to log + return standardized responses
- Always use `handle_route_response(success: bool, data, status_code)` for route returns

### 4. Cache Pattern
Redis caching uses **DTO + Schema validation**:
```python
from app.services.cache_service import cache_get, cache_set
from app.dto.feeds.feed_cache_schema import FeedCacheSchema

# Get with validation
cache_hit = cache_get("feeds")
if cache_hit:
    validated_data = FeedCacheSchema().load(cache_hit)
    
# Set with TTL
cache_set("key", data_dict, ttl=300)
```
**Never** cache raw responses without DTO wrapper. See `feed_service.py` for reference.

### 5. Async Service Layer
All service methods are `async` and use `httpx` for HTTP calls:
```python
async def get_10_feeds(start: int = 0, limit: int = 10) -> List[PostWithComments]:
    posts_data, comments_data = await asyncio.gather(
        send_request(posts_url),
        send_request(comments_url)
    )
```
Use `asyncio.gather()` for concurrent API calls. Routes must be decorated with `@feed_bp.route()` and defined as `async def`.

### 6. Model Construction with `__slots__`
Domain models use `__slots__` for memory efficiency and immutable IDs:
```python
class Post:
    __slots__ = ("_id", "title", "body")
    
    def __init__(self, post_data: dict):
        self._id: int = post_data.get("id")
        
    @property
    def id(self) -> int:
        return self._id  # Read-only
```

## Development Workflow

### Running the Application
```bash
# Local development (SQLite)
python run.py

# Docker (recommended - includes Redis)
docker compose up -d

# Test endpoints
curl http://localhost:5000/api/feeds
curl http://localhost:5000/health
```

### Testing
```bash
# Run all tests
pytest tests/

# Run specific test file
pytest tests/services/feeds/test_send_request.py

# With coverage
pytest --cov=app tests/
```

**Testing conventions:**
- Use `respx.mock` for mocking HTTP calls (see `test_send_request.py`)
- Use `captured_logs` fixture to assert log events: `count_log_events(captured_logs, "service_method")`
- Async tests require `@pytest.mark.asyncio` decorator
- Mock Redis in tests using `unittest.mock.patch`

### Configuration Environments
Set via `FLASK_ENV` environment variable:
- `development` - SQLite, debug mode, localhost Redis
- `testing` - In-memory SQLite, no Redis connection required
- `staging` / `production` - PostgreSQL (requires `DATABASE_URL`)

Config loaded from `config.py` with environment-specific classes.

## Common Pitfalls

1. **Don't put business logic in routes** - Always delegate to services
2. **Don't forget async/await** - Service methods and route handlers calling them must be async
3. **Don't skip schema validation** - All API responses must go through Marshmallow schemas
4. **Don't use `logger.info()` directly** - Use `handle_log()` for consistency
5. **Redis client is lazy-initialized** - Don't call `ping()` during `init_redis()`, let first operation trigger connection
6. **Cache operations use ThreadPoolExecutor** - See `cache_service.py`, operations have timeouts configured via `REDIS_SOCKET_TIMEOUT`

## File Naming Conventions
- Routes: `*_routes.py` with blueprint variable `*_bp`
- Services: `*_service.py` with descriptive function names
- Models: `*_model.py` with class definitions
- Schemas: `*_schemas.py` or `*_schema.py` (DTO schemas in `dto/`)
- Tests: `test_*.py` mirroring app structure

## External Dependencies
- **JSONPlaceholder API** - Mock REST API for posts/comments (`JSONPLACEHOLDER_BASE_URL`)
- **Redis** - Caching layer, runs on `redis:6379` in Docker
- **PostgreSQL** - Production database (not used in development)

## Quick Reference Commands
```bash
# Install dependencies
pip install -r requirements.txt

# Format code
black app/ tests/

# Lint
flake8 app/ tests/

# Check test configuration
pytest --collect-only
```
