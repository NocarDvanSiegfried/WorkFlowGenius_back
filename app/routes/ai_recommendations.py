# routes/ai_recommendations.py
from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from app.database import db
from app.models import AIRecommendation, User, Task
from datetime import datetime

ai_bp = Blueprint('ai', __name__)

@ai_bp.route('/recommendations', methods=['GET'])
@jwt_required()
def get_recommendations():
    """Получить рекомендации ИИ для текущего пользователя"""
    user_id = get_jwt_identity()
    
    # Фильтры
    status = request.args.get('status')
    recommendation_type = request.args.get('type')
    priority = request.args.get('priority')
    
    query = AIRecommendation.query.filter_by(user_id=user_id)
    
    if status:
        query = query.filter_by(status=status)
    if recommendation_type:
        query = query.filter_by(recommendation_type=recommendation_type)
    if priority:
        query = query.filter_by(priority=priority)
    
    recommendations = query.order_by(AIRecommendation.created_at.desc()).all()
    
    return jsonify({
        'success': True,
        'data': [rec.to_dict() for rec in recommendations]
    }), 200

@ai_bp.route('/recommendations/<int:rec_id>/accept', methods=['POST'])
@jwt_required()
def accept_recommendation(rec_id):
    """Принять рекомендацию ИИ"""
    user_id = get_jwt_identity()
    recommendation = AIRecommendation.query.get_or_404(rec_id)
    
    # Проверка прав
    if recommendation.user_id != user_id:
        return jsonify({
            'success': False,
            'message': 'Недостаточно прав'
        }), 403
    
    if recommendation.status != 'pending':
        return jsonify({
            'success': False,
            'message': 'Рекомендация уже обработана'
        }), 400
    
    # Обновление статуса
    recommendation.status = 'accepted'
    recommendation.accepted_at = datetime.utcnow()
    
    # Логика реализации рекомендации (в зависимости от типа)
    if recommendation.recommendation_type == 'task_assignment' and recommendation.task_id:
        # Автоматическое назначение задачи
        # Здесь можно добавить логику назначения
        pass
    
    db.session.commit()
    
    return jsonify({
        'success': True,
        'data': recommendation.to_dict(),
        'message': 'Рекомендация принята'
    }), 200

@ai_bp.route('/recommendations/<int:rec_id>/reject', methods=['POST'])
@jwt_required()
def reject_recommendation(rec_id):
    """Отклонить рекомендацию ИИ"""
    user_id = get_jwt_identity()
    recommendation = AIRecommendation.query.get_or_404(rec_id)
    
    # Проверка прав
    if recommendation.user_id != user_id:
        return jsonify({
            'success': False,
            'message': 'Недостаточно прав'
        }), 403
    
    if recommendation.status != 'pending':
        return jsonify({
            'success': False,
            'message': 'Рекомендация уже обработана'
        }), 400
    
    # Обновление статуса
    recommendation.status = 'rejected'
    
    db.session.commit()
    
    return jsonify({
        'success': True,
        'data': recommendation.to_dict(),
        'message': 'Рекомендация отклонена'
    }), 200

@ai_bp.route('/generate', methods=['POST'])
@jwt_required()
def generate_recommendations():
    """Сгенерировать новые рекомендации ИИ (для админов/менеджеров)"""
    user_id = get_jwt_identity()
    current_user = User.query.get_or_404(user_id)
    
    # Только менеджеры и админы
    if current_user.role not in ['manager', 'admin']:
        return jsonify({
            'success': False,
            'message': 'Недостаточно прав'
        }), 403
    
    # Простая генерация рекомендаций (заглушка)
    # В реальности здесь будет сложная логика анализа данных
    
    # Пример: рекомендация для перегруженных сотрудников
    overloaded_users = User.query.filter(
        User.current_workload >= User.max_workload * 0.9
    ).all()
    
    recommendations_created = 0
    for user in overloaded_users:
        recommendation = AIRecommendation(
            user_id=user.id,
            recommendation_type='workload_adjustment',
            title='Снижение нагрузки',
            description=f'Загруженность составляет {user.current_workload}/{user.max_workload}. Рекомендуется снизить нагрузку.',
            priority='high',
            confidence_score=0.85
        )
        db.session.add(recommendation)
        recommendations_created += 1
    
    db.session.commit()
    
    return jsonify({
        'success': True,
        'message': f'Сгенерировано {recommendations_created} рекомендаций',
        'count': recommendations_created
    }), 201