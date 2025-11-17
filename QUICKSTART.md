# Quick Start Guide

This guide will help you get the Flask API up and running quickly.

## Prerequisites

- Python 3.12 or higher
- pip (Python package manager)

## Installation Steps

### 1. Clone the Repository

```bash
git clone https://github.com/daTaHere/portfolio-sample-api.git
cd portfolio-sample-api
```

### 2. Create Virtual Environment

```bash
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

### 4. Set Up Environment Variables (Optional)

```bash
cp .env.example .env
# Edit .env file with your preferred settings
```

### 5. Run the Application

```bash
python run.py
```

The API will start on `http://localhost:5000`

## Testing the API

### Using curl

**Health Check:**
```bash
curl http://localhost:5000/health
```

**Get All Users:**
```bash
curl http://localhost:5000/api/users
```

**Create a User:**
```bash
curl -X POST http://localhost:5000/api/users \
  -H "Content-Type: application/json" \
  -d '{"name": "John Doe"}'
```

### Using Postman

1. Open Postman
2. Import the following requests:

**GET All Users:**
- Method: `GET`
- URL: `http://localhost:5000/api/users`

**POST Create User:**
- Method: `POST`
- URL: `http://localhost:5000/api/users`
- Headers: `Content-Type: application/json`
- Body (raw JSON):
  ```json
  {
    "name": "Your Name"
  }
  ```

## Running Tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=app --cov-report=term-missing

# Run with verbose output
pytest -v
```

## Production Deployment

### Using Gunicorn

```bash
gunicorn -w 4 -b 0.0.0.0:5000 run:app
```

### Configuration

Set the `FLASK_ENV` environment variable:

```bash
# For production
export FLASK_ENV=production

# For staging
export FLASK_ENV=staging
```

## Troubleshooting

### Database Issues

If you encounter database issues, delete the instance directory and restart:

```bash
rm -rf instance/
python run.py
```

### Port Already in Use

If port 5000 is already in use, specify a different port:

```bash
PORT=8000 python run.py
```

## Project Structure

```
portfolio-sample-api/
├── app/                    # Application package
│   ├── __init__.py        # Flask app factory
│   ├── routes/            # API endpoints
│   ├── models/            # Database models
│   ├── services/          # Business logic
│   └── utils/             # Utility functions
├── tests/                 # Unit tests
├── config.py              # Configuration settings
├── run.py                 # Application entry point
└── requirements.txt       # Python dependencies
```

## Next Steps

- Configure PostgreSQL for production use
- Set up Redis for Celery tasks
- Add authentication and authorization
- Integrate with OpenWeather API
- Integrate with JSONPlaceholder API
- Set up CI/CD pipeline
- Configure monitoring and logging

## Support

For issues and questions, please open an issue on GitHub.
