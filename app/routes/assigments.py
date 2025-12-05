from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from datetime import datetime
from app.database import db
from app.models import Assignment, Task, User

assignments_bp = Blueprint('assignments', __name__)

@assignments_bp.route('', methods=['GET'])
@jwt_required()
def get_assignments():
    """Получить все назначения"""
    user_id = get_jwt_identity()
    current_user = User.query.get_or_404(user_id)
    
    # Фильтры
    status = request.args.get('status')
    task_id = request.args.get('task_id')
    
    # Если сотрудник - показываем только его назначения
    if current_user.role == 'employee':
        query = Assignment.query.filter_by(assigned_to=user_id)
    else:
        query = Assignment.query
    
    if status:
        query = query.filter_by(status=status)
    if task_id:
        query = query.filter_by(task_id=task_id)
    
    assignments = query.all()
    
    return jsonify({
        'success': True,
        'data': [assignment.to_dict() for assignment in assignments]
    }), 200

@assignments_bp.route('/<int:assignment_id>/status', methods=['PUT'])
@jwt_required()
def update_assignment_status(assignment_id):
    """Обновить статус назначения"""
    assignment = Assignment.query.get_or_404(assignment_id)
    user_id = get_jwt_identity()
    current_user = User.query.get_or_404(user_id)
    
    # Проверка прав (только назначенный сотрудник или менеджер)
    if assignment.assigned_to != user_id and current_user.role != 'manager':
        return jsonify({
            'success': False,
            'message': 'Недостаточно прав'
        }), 403
    
    data = request.json
    if not data or 'status' not in data:
        return jsonify({
            'success': False,
            'message': 'Отсутствует поле "status"'
        }), 400
    
    new_status = data['status']
    valid_statuses = ['assigned', 'in_progress', 'completed', 'cancelled']
    
    if new_status not in valid_statuses:
        return jsonify({
            'success': False,
            'message': f'Некорректный статус. Допустимые: {", ".join(valid_statuses)}'
        }), 400
    
    # Обновление статуса
    assignment.status = new_status
    
    # Если задача завершена
    if new_status == 'completed':
        assignment.completed_at = datetime.utcnow()
        
        # Обновить статус задачи
        task = Task.query.get(assignment.task_id)
        if task:
            task.status = 'completed'
            task.updated_at = datetime.utcnow()
    
    db.session.commit()
    
    return jsonify({
        'success': True,
        'data': assignment.to_dict(),
        'message': 'Статус назначения обновлен'
    }), 200