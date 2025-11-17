"""
User routes.
HTTP endpoints for user operations.
"""
from flask import Blueprint, request, jsonify
from app import logger
from app.services.user_service import get_all_users, create_user

user_bp = Blueprint('users', __name__)


@user_bp.route('/users', methods=['GET'])
def get_users():
    """
    GET endpoint to retrieve all users.
    
    Returns:
        JSON: Array of user objects with 200 status code
    """
    try:
        users = get_all_users()
        logger.info('get_users_endpoint', count=len(users))
        return jsonify({
            'success': True,
            'data': users,
            'count': len(users)
        }), 200
    except Exception as e:
        logger.error('get_users_endpoint_error', error=str(e))
        return jsonify({
            'success': False,
            'error': 'Failed to retrieve users'
        }), 500


@user_bp.route('/users', methods=['POST'])
def create_user_endpoint():
    """
    POST endpoint to create a new user.
    
    Request Body:
        {
            "name": "User Name"
        }
    
    Returns:
        JSON: Created user ID with 201 status code
    """
    try:
        data = request.get_json()
        
        if not data or 'name' not in data:
            logger.warning('create_user_endpoint_bad_request', data=data)
            return jsonify({
                'success': False,
                'error': 'Name is required'
            }), 400
        
        name = data['name']
        user_id = create_user(name)
        
        logger.info('create_user_endpoint_success', user_id=user_id, name=name)
        return jsonify({
            'success': True,
            'data': {
                'id': user_id,
                'name': name
            },
            'message': 'User created successfully'
        }), 201
        
    except ValueError as e:
        logger.warning('create_user_endpoint_validation_error', error=str(e))
        return jsonify({
            'success': False,
            'error': str(e)
        }), 400
    except Exception as e:
        logger.error('create_user_endpoint_error', error=str(e))
        return jsonify({
            'success': False,
            'error': 'Failed to create user'
        }), 500
