from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from app.database import db
from app.models import User

users_bp = Blueprint('users', __name__)

@users_bp.route('', methods=['GET'])
@jwt_required()
def get_users():
    """Получить список пользователей"""
    user_id = get_jwt_identity()
    current_user = User.query.get_or_404(user_id)
    
    # Только менеджеры могут видеть всех пользователей
    if current_user.role != 'manager':
        return jsonify({
            'success': False,
            'message': 'Недостаточно прав'
        }), 403
    
    users = User.query.all()
    
    return jsonify({
        'success': True,
        'data': [user.to_dict() for user in users]
    }), 200

@users_bp.route('/<int:user_id>', methods=['GET'])
@jwt_required()
def get_user(user_id):
    """Получить пользователя по ID"""
    current_user_id = get_jwt_identity()
    current_user = User.query.get_or_404(current_user_id)
    
    # Можно видеть свой профиль или быть менеджером
    if current_user_id != user_id and current_user.role != 'manager':
        return jsonify({
            'success': False,
            'message': 'Недостаточно прав'
        }), 403
    
    user = User.query.get_or_404(user_id)
    
    return jsonify({
        'success': True,
        'data': user.to_dict()
    }), 200

@users_bp.route('/<int:user_id>/workload', methods=['GET'])
@jwt_required()
def get_user_workload(user_id):
    """Получить загруженность пользователя"""
    current_user_id = get_jwt_identity()
    current_user = User.query.get_or_404(current_user_id)
    
    # Можно видеть свою загруженность или быть менеджером
    if current_user_id != user_id and current_user.role != 'manager':
        return jsonify({
            'success': False,
            'message': 'Недостаточно прав'
        }), 403
    
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
@jwt_required()
def get_available_users():
    """Получить список доступных пользователей для назначения"""
    user_id = get_jwt_identity()
    current_user = User.query.get_or_404(user_id)
    
    # Только менеджеры
    if current_user.role != 'manager':
        return jsonify({
            'success': False,
            'message': 'Недостаточно прав'
        }), 403
    
    # Пользователи с загруженностью меньше максимума
    users = User.query.filter(
        User.role == 'employee',
        User.current_workload < User.max_workload
    ).order_by(User.current_workload.asc()).all()
    
    return jsonify({
        'success': True,
        'data': [user.to_dict() for user in users]
    }), 200

