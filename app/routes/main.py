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
                'delete': 'DELETE /api/tasks/<id>',
                'assign': 'POST /api/tasks/<id>/assign'
            },
            'users': {
                'list': 'GET /api/users',
                'get': 'GET /api/users/<id>',
                'workload': 'GET /api/users/<id>/workload',
                'available': 'GET /api/users/available'
            },
            'dashboard': {
                'manager': 'GET /api/dashboard/manager',
                'employee': 'GET /api/dashboard/employee'
            },
            'admin': {
                'create_task': 'POST /api/admin/create_task',
                'ai_settings': 'GET /api/admin/ai_settings',
                'analytics': 'GET /api/admin/analytics',
                'teams': 'GET /api/admin/teams',
                'create_teams': 'POST /api/admin/create_teams',
                'system_health': 'GET /api/admin/system_health'
            },
            'health': {
                'check': 'GET /api/health'
            },
            'assignments': {
                'list': 'GET /api/assignments',
                'update_status': 'PUT /api/assignments/<id>/status'
            }
        },
        'authentication': 'JWT Token required for protected endpoints',
        'example_requests': {
            'login': {
                'url': 'POST /api/auth/login',
                'body': {'email': 'user@example.com', 'password': 'password123'}
            },
            'create_task': {
                'url': 'POST /api/tasks',
                'body': {'title': 'New Task', 'priority': 'medium'}
            }
        },
        'status': 'operational',
        'frontend_url': 'http://localhost:5173',
        'cors_enabled': True,
        'documentation': 'dataNoMads'
    })