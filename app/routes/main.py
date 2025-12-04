from flask import Blueprint, jsonify
from datetime import datetime

main_bp = Blueprint('main', __name__)

@main_bp.route('/')
def index():
    return jsonify({
        'success': True,
        'message': 'WorkFlowGenius API',
        'version': '1.0.0',
        'timestamp': datetime.utcnow().isoformat(),
        'api_endpoints': {
            'auth': {
                'login': 'POST /api/auth/login',
                'register': 'POST /api/auth/register',
                'me': 'GET /api/auth/me'
            },
            'tasks': {
                'list': 'GET /api/tasks',
                'create': 'POST /api/tasks',
                'get': 'GET /api/tasks/<id>',
                'update': 'PUT /api/tasks/<id>',
                'delete': 'DELETE /api/tasks/<id>'
            },
            'users': {
                'list': 'GET /api/users',
                'employees': 'GET /api/users/employees',
                'stats': 'GET /api/users/<id>/stats'
            }
        },
        'frontend_url': 'http://localhost:5173',
        'cors_enabled': True
    })