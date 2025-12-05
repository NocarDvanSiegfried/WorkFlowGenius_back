# routes/users.py - ОБНОВЛЕННАЯ ВЕРСИЯ
from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from app.database import db
from app.models import User, PerformanceRecord
from app.services.performance_calculator import calculate_performance

users_bp = Blueprint('users', __name__)

@users_bp.route('', methods=['GET'])
@jwt_required()
def get_users():
    """Получить список пользователей - ОБНОВЛЕННЫЙ"""
    user_id = get_jwt_identity()
    current_user = User.query.get_or_404(user_id)
    
    # Только менеджеры могут видеть всех пользователей
    if current_user.role != 'manager':
        return jsonify({
            'success': False,
            'message': 'Недостаточно прав'
        }), 403
    
    # Фильтры
    role = request.args.get('role')
    min_efficiency = request.args.get('min_efficiency')
    max_workload = request.args.get('max_workload')
    
    query = User.query
    
    if role:
        query = query.filter_by(role=role)
    if min_efficiency:
        query = query.filter(User.efficiency_score >= int(min_efficiency))
    if max_workload:
        query = query.filter(User.current_workload <= int(max_workload))
    
    users = query.all()
    
    return jsonify({
        'success': True,
        'data': [user.to_dict() for user in users]
    }), 200

@users_bp.route('/<int:user_id>', methods=['GET'])
@jwt_required()
def get_user(user_id):
    """Получить пользователя по ID - ОБНОВЛЕННЫЙ"""
    current_user_id = get_jwt_identity()
    current_user = User.query.get_or_404(current_user_id)
    
    # Можно видеть свой профиль или быть менеджером
    if current_user_id != user_id and current_user.role != 'manager':
        return jsonify({
            'success': False,
            'message': 'Недостаточно прав'
        }), 403
    
    user = User.query.get_or_404(user_id)
    
    # Добавляем статистику производительности
    latest_performance = PerformanceRecord.query.filter_by(user_id=user_id)\
        .order_by(PerformanceRecord.period_end.desc()).first()
    
    user_data = user.to_dict()
    if latest_performance:
        user_data['latest_performance'] = latest_performance.to_dict()
    
    return jsonify({
        'success': True,
        'data': user_data
    }), 200

@users_bp.route('/<int:user_id>/workload', methods=['GET'])
@jwt_required()
def get_user_workload(user_id):
    """Получить загруженность пользователя - ОБНОВЛЕННЫЙ"""
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
            'name': user.name,
            'current_workload': user.current_workload,
            'max_workload': user.max_workload,
            'workload_percentage': (user.current_workload / user.max_workload * 100) if user.max_workload > 0 else 0,
            'recommended_max': user.max_workload * 0.9,  # Рекомендуемый максимум 90%
            'available_capacity': max(0, user.max_workload - user.current_workload)
        }
    }), 200

@users_bp.route('/available', methods=['GET'])
@jwt_required()
def get_available_users():
    """Получить список доступных пользователей для назначения - ОБНОВЛЕННЫЙ"""
    user_id = get_jwt_identity()
    current_user = User.query.get_or_404(user_id)
    
    # Только менеджеры
    if current_user.role != 'manager':
        return jsonify({
            'success': False,
            'message': 'Недостаточно прав'
        }), 403
    
    # Пользователи с загруженностью меньше 80% максимума
    users = User.query.filter(
        User.role == 'employee',
        User.current_workload < User.max_workload * 0.8
    ).order_by(
        User.current_workload.asc(),
        User.efficiency_score.desc()
    ).all()
    
    return jsonify({
        'success': True,
        'data': [user.to_dict() for user in users]
    }), 200

@users_bp.route('/<int:user_id>/performance', methods=['GET'])
@jwt_required()
def get_user_performance(user_id):
    """Получить производительность пользователя"""
    current_user_id = get_jwt_identity()
    current_user = User.query.get_or_404(current_user_id)
    
    # Можно видеть свою производительность или быть менеджером
    if current_user_id != user_id and current_user.role != 'manager':
        return jsonify({
            'success': False,
            'message': 'Недостаточно прав'
        }), 403
    
    # Рассчитать текущую производительность
    performance_data = calculate_performance(user_id)
    
    # Исторические данные
    historical_records = PerformanceRecord.query.filter_by(user_id=user_id)\
        .order_by(PerformanceRecord.period_end.desc())\
        .limit(10)\
        .all()
    
    return jsonify({
        'success': True,
        'data': {
            'current_performance': performance_data,
            'historical': [record.to_dict() for record in historical_records],
            'user': {
                'id': user_id,
                'name': User.query.get(user_id).name,
                'efficiency_score': User.query.get(user_id).efficiency_score,
                'satisfaction_score': User.query.get(user_id).satisfaction_score
            }
        }
    }), 200

@users_bp.route('/<int:user_id>/update_scores', methods=['POST'])
@jwt_required()
def update_user_scores(user_id):
    """Обновить оценки пользователя (удовлетворённость, эффективность)"""
    current_user_id = get_jwt_identity()
    current_user = User.query.get_or_404(current_user_id)
    
    # Только менеджеры
    if current_user.role != 'manager':
        return jsonify({
            'success': False,
            'message': 'Недостаточно прав'
        }), 403
    
    data = request.json
    user = User.query.get_or_404(user_id)
    
    if 'satisfaction_score' in data:
        score = int(data['satisfaction_score'])
        if 1 <= score <= 10:
            user.satisfaction_score = score
    
    if 'efficiency_score' in data:
        score = int(data['efficiency_score'])
        if 1 <= score <= 10:
            user.efficiency_score = score
    
    if 'monthly_hours' in data:
        user.monthly_hours = int(data['monthly_hours'])
    
    if 'salary' in data:
        user.salary = int(data['salary'])
    
    if 'position' in data:
        user.position = data['position']
    
    db.session.commit()
    
    return jsonify({
        'success': True,
        'data': user.to_dict(),
        'message': 'Данные пользователя обновлены'
    }), 200
@users_bp.route('/me', methods=['GET'])
@jwt_required()
def redirect_to_auth_me():
    """Redirect с /users/me на /auth/me для совместимости"""
    from flask import redirect
    return redirect('/api/auth/me', code=302)