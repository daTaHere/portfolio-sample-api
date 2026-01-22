# Portfolio Sample API

[![Python](https://img.shields.io/badge/Python-3.12+-blue)](https://www.python.org/)
[![Flask](https://img.shields.io/badge/Flask-3.x-greenyellow)](https://flask.palletsprojects.com/)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-15+-magenta)](https://www.postgresql.org/)
[![Redis](https://img.shields.io/badge/Redis-8+-red)](https://redis.io/)
[![Docker](https://img.shields.io/badge/Docker-Ready-blue)](https://www.docker.com/)
[![Pytest](https://img.shields.io/badge/Tests-pytest-green)](https://docs.pytest.org/)
[![CI](https://github.com/daTaHere/portfolio-samples/actions/workflows/ci.yml/badge.svg?branch=main)](https://github.com/daTaHere/portfolio-samples/actions/workflows/ci.yml)


A **production-grade Flask backend API** built with industry best practices.  
This project demonstrates **third-party API integration**, **async service orchestration**, **domain-driven modeling**, and **system optimization via Redis caching**.

The architecture emphasizes **clean separation of concerns**, **structured logging**, **validation-first design**, and **testability**, targeting **medium-to-large scale backend systems**.

> ⚠️ **Status:**  Weather API complete and fully tested. Core service layer hardened. Ongoing: refactor and harden feeds service layer, route layer, and unit tests.

---

## ✨ Features

- **Async-compatible** service layer using **httpx** and **asyncio** for I/O-bound workloads
- **Redis-backed caching** with explicit DTO + schema validation
- **Marshmallow** input/output validation enforcing service and API contracts
- **Structured logging** (structlog-style) for observability
- **SQLAlchemy ORM** with environment-aware database configuration
- **SQLite** for local development, **PostgreSQL** for staging/production
- **Docker & Docker Compose** for dev/prod parity
- **Celery + Redis** ready for background task processing
- Centralized **exception handling** and error modeling
- Comprehensive **Unit Tests** for service and route layers, including async external calls
- **Services** are allowed to raise domain exceptions; routes translate them to HTTP response

---

## ⚙️ Technology Stack

### Core Stack
| Layer            | Technology                     |
|------------------|--------------------------------|
| Language         | Python 3.12                    |
| Framework        | Flask (Blueprints, App Factory)|
| Async I/O        | asyncio / httpx                |
| ORM              | SQLAlchemy / Flask-SQLAlchemy  |
| Validation       | Marshmallow                    |
| Caching          | Redis                          |
| Background Jobs  | Celery + Redis                 |
| Database         | SQLite (dev), PostgreSQL (prod)|
| Logging          | structlog                      |
| Testing          | pytest, respx, coverage        |
| Containerization | Docker, Docker Compose         |

---

## 🧱 Project Structure

The project follows a **layered, service-oriented architecture**:

```
portfolio-sample-api/
├── app/                        # Application package
│   ├── __init__.py             # App factory
│   ├── clients/                # External service & cache clients
│   │   └── redis_client.py
│   ├── dto/                    # DTOs for caching & feature separation
│   ├── exceptions/             # Domain & HTTP custom exceptions
│   ├── models/                 # ORM & domain models
│   ├── routes/                 # HTTP layer / endpoint controller (Blueprints)
│   ├── schemas/                # Marshmallow schemas for I/O validation
│   ├── services/               # Business logic & orchestration
│   │   ├── feeds
│   │   ├── users
│   │   └── weather
│   ├── tasks/                  # Background schedulers / Celery tasks
│   ├── utils/                  # Shared helpers
│   │   └── logger_helper.py
│   └── logging.py              # Logging configuration
├── tests/                      # Unit & integration tests
├── instance/                   # Local SQLite DB (auto-generated)
├── config.py                   # Environment-based config
├── run.py                      # Application entry point
├── requirements.txt
└── .env.example
```
---

### Architectural Rules
- **Routes** handle HTTP only (no business logic)
- **Services** orchestrate workflows and domain rules
- **DTOs** define internal data boundaries
- **Schemas** validate all inbound and outbound data
- **Clients** isolate external systems (Redis, APIs)

---

## 🚀 Quickstart

### Prerequisites
- Python 3.12+
- pip
- Docker & Docker Compose (recommended)
- Redis (for caching / Celery)

### Local Development
1. Install
```bash
git clone https://github.com/daTaHere/portfolio-sample-api.git
cd portfolio-sample-api
```
2. Setup environment
```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
```
3. Run application
```bash
python run.py
```

### Docker (Recommended)
```bash
docker compose up -d
```

### Test API
```bash
curl http://localhost:5000/api/feeds
```

---

## 🧪 Testing
```bash
pytest tests/
```
- Service and route layers tested independently
- Async external calls mocked with `respx`
- Schema validation asserted in tests
- Designed for refactor safety

### Testing Philosophy
- Services are tested as behavior units, not implementation details
- External systems (HTTP, cache, geo-IP) are always mocked
- Validation and exception paths are explicitly asserted
- Logging is treated as part of the contract and verified in tests

## 🌍 Environment Configuration

### Supported environments:
- `development` – local SQLite
- `testing` – in-memory SQLite
- `staging` – PostgreSQL
- `production` – PostgreSQL

```bash
export FLASK_ENV=production
```

---

## 🗺️ Roadmap / Future Enhancements
- Cache invalidation strategies & metrics
- Auth & RBAC
- Rate limiting
- CI/CD hardening
- Load testing & benchmarking
- Production monitoring & alerting

---

## 👨‍💻 Author

**Adam Huynh**  
[🌐 adamhuynh.dev](https://adamhuynh.dev)  
Full Stack Engineer  
React • TypeScript • Python • C# • Flask/Django • ASP.NET Core • SQL • DevOps • Cloud Architecture

---

## 📫 Contact

I’m always open to discussing new opportunities, collaboration, or technical deep dives.

- 🌐 **Portfolio:** [adamhuynh.dev](https://adamhuynh.dev)
- 💼 **LinkedIn:** [linkedin.com/in/adam-huynh](https://www.linkedin.com/in/adam-huynh-1a241a211)
- 📧 **Email:** adam@adamhuynh.dev
