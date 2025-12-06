"""
API endpoints для аналитики
"""
from flask import Blueprint, request, jsonify

from app.models import User
from app.services.analytics_service import get_team_analytics, get_employee_metrics, get_model_metrics

analytics_bp = Blueprint('analytics', __name__)


@analytics_bp.route('/team', methods=['GET'])
def get_analytics():
    """Получить аналитику команды"""
    # Без авторизации - просто возвращаем аналитику
    days = int(request.args.get('days', 30))
    analytics = get_team_analytics(days=days)
    
    return jsonify({
        'success': True,
        'data': analytics
    }), 200


@analytics_bp.route('/employee/<int:employee_id>', methods=['GET'])
def get_employee_analytics(employee_id):
    """Получить аналитику сотрудника"""
    # Без авторизации - просто возвращаем аналитику сотрудника
    
    days = int(request.args.get('days', 30))
    metrics = get_employee_metrics(employee_id, days=days)
    
    if not metrics:
        return jsonify({
            'success': False,
            'message': 'Сотрудник не найден'
        }), 404
    
    return jsonify({
        'success': True,
        'data': metrics
    }), 200


@analytics_bp.route('/model', methods=['GET'])
def get_model_analytics():
    """Получить метрики ИИ модели"""
    # Без авторизации - просто возвращаем метрики модели
    metrics = get_model_metrics()
    
    return jsonify({
        'success': True,
        'data': metrics
    }), 200

