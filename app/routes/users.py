from flask import Blueprint, request, jsonify

from app.database import db
from app.models import User

users_bp = Blueprint('users', __name__)

@users_bp.route('', methods=['GET'])
def get_users():
    """Получить список пользователей"""
    # Без авторизации - просто возвращаем всех пользователей
    
    users = User.query.all()
    
    return jsonify({
        'success': True,
        'data': [user.to_dict() for user in users]
    }), 200

@users_bp.route('/<int:user_id>', methods=['GET'])
def get_user(user_id):
    """Получить пользователя по ID"""
    # Без авторизации - просто возвращаем пользователя
    
    user = User.query.get_or_404(user_id)
    
    return jsonify({
        'success': True,
        'data': user.to_dict()
    }), 200

@users_bp.route('/<int:user_id>/workload', methods=['GET'])
def get_user_workload(user_id):
    """Получить загруженность пользователя"""
    # Без авторизации - просто возвращаем загруженность
    
    user = User.query.get_or_404(user_id)
    
    return jsonify({
        'success': True,
        'data': {
            'user_id': user.id,
            'current_workload': user.current_workload,
            'max_workload': user.max_workload,
            'workload_percentage': (user.current_workload / user.max_workload * 100) if user.max_workload > 0 else 0
        }
    }), 200

@users_bp.route('/available', methods=['GET'])
def get_available_users():
    """Получить список доступных пользователей для назначения"""
    # Без авторизации - просто возвращаем доступных пользователей
    
    # Пользователи с загруженностью меньше максимума
    users = User.query.filter(
        User.role == 'employee',
        User.current_workload < User.max_workload
    ).order_by(User.current_workload.asc()).all()
    
    return jsonify({
        'success': True,
        'data': [user.to_dict() for user in users]
    }), 200

