"""
Unit tests for user service and routes.
"""
import pytest
import sys
import os

# Add project root to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app import create_app, db
from app.models.user_model import User


@pytest.fixture
def app():
    """Create and configure a test application instance."""
    app = create_app('testing')
    
    with app.app_context():
        db.create_all()
        yield app
        db.session.remove()
        db.drop_all()


@pytest.fixture
def client(app):
    """Create a test client."""
    return app.test_client()


def test_health_check(client):
    """Test health check endpoint."""
    response = client.get('/health')
    assert response.status_code == 200
    data = response.get_json()
    assert data['status'] == 'healthy'


def test_get_users_empty(client):
    """Test GET /api/users with empty database."""
    response = client.get('/api/users')
    assert response.status_code == 200
    data = response.get_json()
    assert data['success'] is True
    assert data['count'] == 0
    assert data['data'] == []


def test_create_user(client):
    """Test POST /api/users to create a new user."""
    response = client.post('/api/users', json={'name': 'John Doe'})
    assert response.status_code == 201
    data = response.get_json()
    assert data['success'] is True
    assert data['data']['name'] == 'John Doe'
    assert 'id' in data['data']


def test_create_user_without_name(client):
    """Test POST /api/users without name field."""
    response = client.post('/api/users', json={})
    assert response.status_code == 400
    data = response.get_json()
    assert data['success'] is False


def test_create_user_with_empty_name(client):
    """Test POST /api/users with empty name."""
    response = client.post('/api/users', json={'name': ''})
    assert response.status_code == 400
    data = response.get_json()
    assert data['success'] is False


def test_get_users_after_creation(client):
    """Test GET /api/users after creating users."""
    # Create two users
    client.post('/api/users', json={'name': 'Alice'})
    client.post('/api/users', json={'name': 'Bob'})
    
    # Get all users
    response = client.get('/api/users')
    assert response.status_code == 200
    data = response.get_json()
    assert data['success'] is True
    assert data['count'] == 2
    assert len(data['data']) == 2
