# app/routes/main.py
from flask import Blueprint, jsonify
from datetime import datetime

main_bp = Blueprint('main', __name__)

@main_bp.route('/')
def index():
    return jsonify({
        'success': True,
        'message': 'VK TaskFlow API',
        'version': '2.0.0',
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
                'assign': 'POST /api/tasks/<id>/assign',
                'urgent': 'GET /api/tasks/urgent',
                'queue': 'GET /api/tasks/queue',
                'recommendations': 'GET /api/tasks/<id>/recommendations'
            },
            'users': {
                'list': 'GET /api/users',
                'get': 'GET /api/users/<id>',
                'workload': 'GET /api/users/<id>/workload',
                'performance': 'GET /api/users/<id>/performance',
                'available': 'GET /api/users/available',
                'update_scores': 'POST /api/users/<id>/update_scores'
            },
            'assignments': {
                'list': 'GET /api/assignments',
                'update_status': 'PUT /api/assignments/<id>/status'
            },
            'analytics': {
                'weekly': 'GET /api/analytics/weekly',
                'team_performance': 'GET /api/analytics/team_performance'
            },
            'ai': {
                'recommendations': 'GET /api/ai/recommendations',
                'accept': 'POST /api/ai/recommendations/<id>/accept',
                'reject': 'POST /api/ai/recommendations/<id>/reject',
                'generate': 'POST /api/ai/generate'
            },
            'skills': {
                'list': 'GET /api/skills',
                'create': 'POST /api/skills',
                'user_skills': 'GET /api/skills/user/<id>',
                'add_skill': 'POST /api/skills/user/<id>',
                'remove_skill': 'DELETE /api/skills/user/<user_skill_id>'
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
            }
        },
        'features': [
            'AI-powered task distribution',
            'Real-time performance analytics',
            'Skill-based assignment',
            'Manager and employee dashboards',
            'Weekly performance reports',
            'AI recommendations',
            'Team workload monitoring',
            'Urgent task prioritization'
        ],
        'authentication': 'JWT Token required for protected endpoints',
        'example_requests': {
            'login': {
                'url': 'POST /api/auth/login',
                'body': {'email': 'user@example.com', 'password': 'password123'}
            },
            'create_task': {
                'url': 'POST /api/tasks',
                'body': {'title': 'New Task', 'priority': 'medium', 'description': 'Task description'}
            },
            'get_dashboard': {
                'url': 'GET /api/dashboard/employee',
                'headers': {'Authorization': 'Bearer <token>'}
            }
        },
        'status': 'operational',
        'project_name': 'VK TaskFlow',
        'frontend_url': 'http://localhost:5173',
        'cors_enabled': True,
        'documentation': 'Full API documentation available at / endpoint'
    })