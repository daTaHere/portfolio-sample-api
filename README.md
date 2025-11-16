# Portfolio Sample API

A production-grade Flask backend API built with industry best practices. This application demonstrates a robust Flask architecture with structured logging, database ORM, async task queuing, and comprehensive error handling suitable for medium to large-scale enterprise applications.

## Features

- **RESTful API** with user management endpoints
- **Production-ready architecture** using Flask app factory pattern
- **Multiple environment support** (development, staging, production, testing)
- **Structured logging** with structlog for monitoring and debugging
- **Database ORM** with SQLAlchemy/Flask-SQLAlchemy
- **SQLite** for development, **PostgreSQL** for staging/production
- **CORS support** for cross-origin requests
- **Async task queue** ready with Celery + Redis
- **Comprehensive error handling** and validation
- **Unit testing** with pytest and coverage
- **WSGI production server** with gunicorn

## Technology Stack

- **Python 3.12** - Backend language
- **Flask** - Lightweight web framework
- **Flask-CORS** - Handle cross-origin requests
- **SQLAlchemy / Flask-SQLAlchemy** - ORM for database access
- **PostgreSQL** - Relational database (production)
- **SQLite** - Local development database
- **psycopg2-binary** - PostgreSQL driver
- **gunicorn** - Production WSGI server
- **python-dotenv** - Environment variable management
- **Celery** - Async task queue
- **Redis** - Broker for Celery tasks
- **pytest + coverage** - Unit testing and coverage
- **structlog** - Structured logging for monitoring

## Project Structure

```
portfolio-sample-api/
├── app/
│   ├── __init__.py           # Flask app factory
│   ├── routes/
│   │   ├── __init__.py
│   │   └── user_routes.py    # User endpoints
│   ├── models/
│   │   ├── __init__.py
│   │   └── user_model.py     # User data model
│   ├── services/
│   │   ├── __init__.py
│   │   └── user_service.py   # Business logic
│   └── utils/
│       └── __init__.py
├── tests/
│   ├── __init__.py
│   └── test_user_routes.py   # Unit tests
├── instance/                  # SQLite database (auto-generated)
├── config.py                  # Configuration settings
├── run.py                     # Application entry point
├── requirements.txt           # Python dependencies
└── .env.example              # Environment variables template
```

## Getting Started

### Prerequisites

- Python 3.12+
- pip (Python package manager)
- (Optional) PostgreSQL for staging/production
- (Optional) Redis for Celery async tasks

### Installation

1. Clone the repository
```bash
git clone https://github.com/daTaHere/portfolio-sample-api.git
cd portfolio-sample-api
```

2. Create a virtual environment
```bash
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies
```bash
pip install -r requirements.txt
```

4. Set up environment variables
```bash
cp .env.example .env
# Edit .env with your configuration
```

### Running the Application

#### Development Mode

```bash
python run.py
```

The API will start on `http://localhost:5000`

#### Production Mode with Gunicorn

```bash
gunicorn -w 4 -b 0.0.0.0:5000 run:app
```

## API Endpoints

### Health Check

```
GET /health
```

Returns the health status of the API.

**Response:**
```json
{
  "status": "healthy",
  "service": "portfolio-sample-api"
}
```

### Get All Users

```
GET /api/users
```

Retrieves all users from the database.

**Response:**
```json
{
  "success": true,
  "data": [
    {
      "id": 1,
      "name": "John Doe",
      "created_at": "2024-01-01T12:00:00"
    }
  ],
  "count": 1
}
```

### Create User

```
POST /api/users
```

Creates a new user.

**Request Body:**
```json
{
  "name": "Jane Smith"
}
```

**Response:**
```json
{
  "success": true,
  "data": {
    "id": 2,
    "name": "Jane Smith"
  },
  "message": "User created successfully"
}
```

## Testing

Run the test suite:

```bash
pytest
```

Run with coverage report:

```bash
pytest --cov=app --cov-report=html
```

## Testing with Postman

1. Start the application: `python run.py`
2. Import the following requests into Postman:

**GET All Users:**
- Method: GET
- URL: `http://localhost:5000/api/users`

**Create User:**
- Method: POST
- URL: `http://localhost:5000/api/users`
- Headers: `Content-Type: application/json`
- Body (raw JSON):
  ```json
  {
    "name": "Test User"
  }
  ```

## Environment Configuration

The application supports multiple environments:

- **development** - Local development with SQLite
- **staging** - Pre-production with PostgreSQL
- **production** - Production environment with PostgreSQL
- **testing** - Automated testing with in-memory SQLite

Set the environment using the `FLASK_ENV` variable:

```bash
export FLASK_ENV=production
```

## Database Setup

### Development (SQLite)

SQLite database is automatically created in the `instance/` directory when you first run the application.

### Production (PostgreSQL)

1. Install PostgreSQL
2. Create a database
3. Update `DATABASE_URL` in your `.env` file:
   ```
   DATABASE_URL=postgresql://username:password@localhost:5432/database_name
   ```

## Security Features

- Environment-based configuration management
- Secure session cookies in production
- SQL injection prevention via SQLAlchemy ORM
- Input validation and sanitization
- Comprehensive error handling
- Structured logging for audit trails

## Future Enhancements

- Integration with OpenWeather API
- Integration with JSONPlaceholder API
- User authentication and authorization
- Rate limiting
- API documentation with Swagger/OpenAPI
- Docker containerization
- CI/CD pipeline setup
- Monitoring and alerting integration

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Contributing

1. Fork the repository
2. Create a feature branch
3. Commit your changes
4. Push to the branch
5. Open a Pull Request
