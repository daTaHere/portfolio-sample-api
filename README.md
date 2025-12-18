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

> ⚠️ **Status:** Actively developed. Core architecture and service layer are stable.

---

## ✨ Features

- Fully **async service layer** for scalable I/O-bound workloads
- **Redis-backed caching** with explicit DTO + schema validation
- **Marshmallow** input/output validation enforcing API contracts
- **Structured logging** (structlog-style) for observability
- **SQLAlchemy ORM** with environment-aware database configuration
- **SQLite** for local development, **PostgreSQL** for staging/production
- **Docker & Docker Compose** for dev/prod parity
- **Celery + Redis** ready for background task processing
- Centralized **exception handling** and error modeling
- **Unit tests** covering service and route layers with async mocking

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
├── app/
│ ├── __init__.py                   # App factory
│ ├── clients/                  # External service & cache clients
│ │ └── redis_routes.py
│ ├── exceptions/               # Domain & HTTP exception modeling
│ │ ├── base.py
│ │ └── exception_handlers.py
│ ├── schemas/                  # Marshmallow schemas (I/O validation)
│ ├── models/                   # ORM & domain models
│ ├── dto/                      # Internal data transfer objects
│ ├── routes/                   # HTTP layer (Blueprints)
│ ├── services/                 # Business logic & orchestration
│ ├── utils/                    # Shared helpers             
│ |  └── logger_helper.py
│ ├── logging.py                # Logging configuration
│
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
flask run.py
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
- OpenWeather & JSONPlaceholder integrations
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
React • TypeScript • Python • C# 
• Flask/Django • ASP.NET Core • SQL 
• DevOps • Cloud Architecture

---

## 📫 Contact

I’m always open to discussing new opportunities, collaboration, or technical deep dives.

- 🌐 **Portfolio:** [adamhuynh.dev](https://adamhuynh.dev)
- 💼 **LinkedIn:** [linkedin.com/in/adam-huynh](https://www.linkedin.com/in/adam-huynh-1a241a211)
- 📧 **Email:** adam@adamhuynh.dev
