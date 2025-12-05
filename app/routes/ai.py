from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from datetime import datetime
from app.database import db
from app.models import AIRecommendation, User, Task, Assignment
from app.services.ai_recommender import generate_task_recommendations
from app.services.ml_service import ml_service

ai_bp = Blueprint('ai', __name__)

@ai_bp.route('/recommendations', methods=['GET'])
@jwt_required()
def get_recommendations():
    """Получить рекомендации ИИ"""
    user_id = get_jwt_identity()
    current_user = User.query.get_or_404(user_id)
    
    # Фильтры
    status = request.args.get('status', 'pending')
    recommendation_type = request.args.get('type')
    limit = request.args.get('limit', 20, type=int)
    
    query = AIRecommendation.query
    
    # Если сотрудник - показываем только его рекомендации
    if current_user.role == 'employee':
        query = query.filter_by(user_id=user_id)
    
    if status:
        query = query.filter_by(status=status)
    if recommendation_type:
        query = query.filter_by(recommendation_type=recommendation_type)
    
    recommendations = query.order_by(
        AIRecommendation.priority.desc(),
        AIRecommendation.confidence_score.desc(),
        AIRecommendation.created_at.desc()
    ).limit(limit).all()
    
    return jsonify({
        'success': True,
        'data': [rec.to_dict() for rec in recommendations],
        'count': len(recommendations),
        'ml_model_loaded': ml_service.is_loaded
    }), 200

@ai_bp.route('/recommendations/<int:recommendation_id>/accept', methods=['POST'])
@jwt_required()
def accept_recommendation(recommendation_id):
    """Принять рекомендацию ИИ"""
    recommendation = AIRecommendation.query.get_or_404(recommendation_id)
    user_id = get_jwt_identity()
    current_user = User.query.get_or_404(user_id)
    
    # Проверка прав
    if recommendation.user_id != user_id and current_user.role != 'manager':
        return jsonify({
            'success': False,
            'message': 'Недостаточно прав'
        }), 403
    
    if recommendation.status != 'pending':
        return jsonify({
            'success': False,
            'message': 'Рекомендация уже обработана'
        }), 400
    
    recommendation.status = 'accepted'
    recommendation.accepted_at = datetime.utcnow()
    
    # Выполняем действие в зависимости от типа рекомендации
    if recommendation.recommendation_type == 'task_assignment' and recommendation.task_id:
        task = Task.query.get(recommendation.task_id)
        if task and task.status == 'pending':
            # Создаем назначение
            assignment = Assignment(
                task_id=task.id,
                assigned_to=recommendation.user_id,
                assigned_by=user_id if current_user.role == 'manager' else recommendation.user_id,
                workload_points=10,
                status='assigned'
            )
            
            # Обновляем статус задачи
            task.status = 'assigned'
            task.updated_at = datetime.utcnow()
            
            # Обновляем загруженность сотрудника
            employee = User.query.get(recommendation.user_id)
            if employee:
                employee.current_workload = min(
                    employee.current_workload + 10,
                    employee.max_workload
                )
            
            db.session.add(assignment)
    
    db.session.commit()
    
    return jsonify({
        'success': True,
        'data': recommendation.to_dict(),
        'message': 'Рекомендация принята и выполнена'
    }), 200

@ai_bp.route('/recommendations/<int:recommendation_id>/reject', methods=['POST'])
@jwt_required()
def reject_recommendation(recommendation_id):
    """Отклонить рекомендацию ИИ"""
    recommendation = AIRecommendation.query.get_or_404(recommendation_id)
    user_id = get_jwt_identity()
    current_user = User.query.get_or_404(user_id)
    
    # Проверка прав
    if recommendation.user_id != user_id and current_user.role != 'manager':
        return jsonify({
            'success': False,
            'message': 'Недостаточно прав'
        }), 403
    
    if recommendation.status != 'pending':
        return jsonify({
            'success': False,
            'message': 'Рекомендация уже обработана'
        }), 400
    
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
    """Сгенерировать новые рекомендации ИИ"""
    user_id = get_jwt_identity()
    current_user = User.query.get_or_404(user_id)
    
    if current_user.role != 'manager':
        return jsonify({
            'success': False,
            'message': 'Недостаточно прав'
        }), 403
    
    data = request.json
    recommendation_type = data.get('type', 'task_assignment')
    
    if recommendation_type == 'task_assignment':
        # Получаем задачи без назначения
        tasks = Task.query.filter_by(status='pending').all()
        
        # Получаем сотрудников
        employees = User.query.filter_by(role='employee').all()
        
        if not tasks or not employees:
            return jsonify({
                'success': False,
                'message': 'Нет задач или сотрудников для генерации рекомендаций'
            }), 400
        
        # Генерируем рекомендации
        recommendations = generate_task_recommendations(tasks, employees)
        
        # Сохраняем рекомендации в БД
        created_count = 0
        for rec in recommendations:
            # Проверяем, нет ли уже такой рекомендации
            existing = AIRecommendation.query.filter_by(
                user_id=rec['user_id'],
                task_id=rec['task_id'],
                status='pending'
            ).first()
            
            if not existing:
                ai_rec = AIRecommendation(
                    user_id=rec['user_id'],
                    task_id=rec['task_id'],
                    recommendation_type='task_assignment',
                    title=rec['title'],
                    description=rec['description'],
                    priority=rec['priority'],
                    confidence_score=rec['confidence']
                )
                db.session.add(ai_rec)
                created_count += 1
        
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': f'Сгенерировано {created_count} рекомендаций по назначению задач',
            'count': created_count,
            'ml_model_used': ml_service.is_loaded
        }), 200
    
    return jsonify({
        'success': False,
        'message': f'Тип генерации "{recommendation_type}" не поддерживается'
    }), 400

@ai_bp.route('/predict_suitability', methods=['POST'])
@jwt_required()
def predict_suitability():
    """Предсказать совместимость сотрудника и задачи (для тестирования ML)"""
    user_id = get_jwt_identity()
    current_user = User.query.get_or_404(user_id)
    
    if current_user.role != 'manager':
        return jsonify({
            'success': False,
            'message': 'Недостаточно прав'
        }), 403
    
    data = request.json
    
    if not data or 'employee_id' not in data or 'task_id' not in data:
        return jsonify({
            'success': False,
            'message': 'Укажите employee_id и task_id'
        }), 400
    
    employee = User.query.get_or_404(data['employee_id'])
    task = Task.query.get_or_404(data['task_id'])
    
    # Подготовка данных для ML
    employee_data = {
        'satisfaction': employee.satisfaction_score,
        'evaluation': employee.efficiency_score,
        'projects_count': employee.current_workload // 10 + 1,
        'monthly_hours': employee.monthly_hours,
        'salary': employee.salary,
        'skills': employee.skills[0].skill_name if employee.skills else 'Python',
        'efficiency': employee.efficiency_score
    }
    
    task_data = {
        'description': task.title,
        'complexity': 'High' if task.priority == 'urgent' else 'Medium',
        'priority': task.priority
    }
    
    # Предсказание
    suitability_score = ml_service.predict_suitability(employee_data, task_data)
    
    return jsonify({
        'success': True,
        'data': {
            'employee': {
                'id': employee.id,
                'name': employee.name,
                'position': employee.position,
                'efficiency_score': employee.efficiency_score,
                'satisfaction_score': employee.satisfaction_score,
                'skills': [skill.skill_name for skill in employee.skills]
            },
            'task': {
                'id': task.id,
                'title': task.title,
                'priority': task.priority,
                'status': task.status
            },
            'suitability_score': suitability_score,
            'confidence': suitability_score,
            'recommendation': 'Рекомендуется' if suitability_score > 0.6 else 'Не рекомендуется',
            'ml_model_loaded': ml_service.is_loaded
        }
    }), 200