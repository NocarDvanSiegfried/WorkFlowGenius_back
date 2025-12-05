from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from datetime import datetime
from app.database import db
from app.models import Task, Assignment, User
from app.schemas.task_schema import TaskSchema, CreateTaskSchema
from app.services.task_distributor import assign_task_automatically

tasks_bp = Blueprint('tasks', __name__)

@tasks_bp.route('', methods=['GET'])
@jwt_required()
def get_tasks():
    """Получить список задач"""
    user_id = get_jwt_identity()
    user = User.query.get_or_404(user_id)
    
    # Фильтры
    status = request.args.get('status')
    assigned_to = request.args.get('assigned_to')
    
    # Если сотрудник - показываем только его задачи
    if user.role == 'employee':
        query = db.session.query(Task).join(Assignment).filter(Assignment.assigned_to == user_id)
    # Если менеджер - показываем все задачи
    elif user.role == 'manager':
        query = Task.query
        if assigned_to:
            query = query.join(Assignment).filter(Assignment.assigned_to == assigned_to)
    else:
        query = Task.query.filter_by(created_by=user_id)
    
    if status:
        query = query.filter(Task.status == status)
    
    tasks = query.all()
    
    schema = TaskSchema(many=True)
    return jsonify({
        'success': True,
        'data': schema.dump(tasks)
    }), 200

@tasks_bp.route('', methods=['POST'])
@jwt_required()
def create_task():
    """Создать задачу"""
    if not request.json:
        return jsonify({
            'success': False,
            'message': 'Отсутствуют данные'
        }), 400
    
    # ПРОСТАЯ ВАЛИДАЦИЯ ВМЕСТО СХЕМ (на время тестирования)
    data = request.json
    
    if 'title' not in data:
        return jsonify({
            'success': False,
            'message': 'Отсутствует поле "title"'
        }), 400
    
    user_id = get_jwt_identity()
    
    # Парсинг deadline если это строка
    deadline = data.get('deadline')
    if deadline and isinstance(deadline, str):
        try:
            from datetime import datetime
            deadline = datetime.fromisoformat(deadline.replace('Z', '+00:00'))
        except (ValueError, AttributeError):
            deadline = None
    
    # Создание задачи
    task = Task(
        title=data['title'],
        description=data.get('description'),
        priority=data.get('priority', 'medium'),
        deadline=deadline,
        estimated_hours=data.get('estimated_hours'),
        created_by=user_id
    )
    
    db.session.add(task)
    db.session.flush()
    
    # Автоматическое назначение задачи (если включено)
    try:
        from app.services.task_distributor import assign_task_automatically
        assignment = assign_task_automatically(task.id, user_id)
        
        if assignment:
            task.status = 'pending'
    except Exception as e:
        print(f"Ошибка автоматического назначения: {e}")
        # Продолжаем без назначения
    
    db.session.commit()
    
    return jsonify({
        'success': True,
        'data': task.to_dict(),
        'message': 'Задача успешно создана'
    }), 201

@tasks_bp.route('/<int:task_id>', methods=['GET'])
@jwt_required()
def get_task(task_id):
    """Получить задачу по ID"""
    task = Task.query.get_or_404(task_id)
    
    schema = TaskSchema()
    return jsonify({
        'success': True,
        'data': schema.dump(task)
    }), 200

@tasks_bp.route('/<int:task_id>', methods=['PUT'])
@jwt_required()
def update_task(task_id):
    """Обновить задачу"""
    task = Task.query.get_or_404(task_id)
    user_id = get_jwt_identity()
    
    # Проверка прав (только создатель или менеджер)
    if task.created_by != user_id:
        user = User.query.get(user_id)
        if user.role != 'manager':
            return jsonify({
                'success': False,
                'message': 'Недостаточно прав'
            }), 403
    
    schema = TaskSchema()
    try:
        data = schema.load(request.json, partial=True)
    except Exception as e:
        return jsonify({
            'success': False,
            'message': 'Ошибка валидации',
            'errors': str(e)
        }), 400
    
    # Обновление полей
    for key, value in data.items():
        if hasattr(task, key) and key not in ['id', 'created_by', 'created_at', 'updated_at']:
            # Парсинг deadline если это строка
            if key == 'deadline' and isinstance(value, str):
                try:
                    value = datetime.fromisoformat(value.replace('Z', '+00:00'))
                except (ValueError, AttributeError):
                    value = None
            setattr(task, key, value)
    
    db.session.commit()
    
    return jsonify({
        'success': True,
        'data': schema.dump(task),
        'message': 'Задача успешно обновлена'
    }), 200

@tasks_bp.route('/<int:task_id>', methods=['DELETE'])
@jwt_required()
def delete_task(task_id):
    """Удалить задачу"""
    task = Task.query.get_or_404(task_id)
    user_id = get_jwt_identity()
    
    # Проверка прав
    if task.created_by != user_id:
        user = User.query.get(user_id)
        if user.role != 'manager':
            return jsonify({
                'success': False,
                'message': 'Недостаточно прав'
            }), 403
    
    db.session.delete(task)
    db.session.commit()
    
    return jsonify({
        'success': True,
        'message': 'Задача успешно удалена'
    }), 200

@tasks_bp.route('/<int:task_id>/assign', methods=['POST'])
@jwt_required()
def assign_task(task_id):
    """Автоматически назначить задачу"""
    task = Task.query.get_or_404(task_id)
    user_id = get_jwt_identity()
    
    # Проверка прав
    if task.created_by != user_id:
        user = User.query.get(user_id)
        if user.role != 'manager':
            return jsonify({
                'success': False,
                'message': 'Недостаточно прав'
            }), 403
    
    # Проверка: задача уже назначена?
    existing_assignment = Assignment.query.filter_by(task_id=task_id, status='assigned').first()
    if existing_assignment:
        return jsonify({
            'success': False,
            'message': 'Задача уже назначена',
            'data': existing_assignment.to_dict()
        }), 400
    
    # Автоматическое назначение
    assignment = assign_task_automatically(task_id, user_id)
    
    if not assignment:
        return jsonify({
            'success': False,
            'message': 'Нет доступных сотрудников для назначения'
        }), 400
    
    task.status = 'assigned'
    db.session.commit()
    
    return jsonify({
        'success': True,
        'data': assignment.to_dict(),
        'message': 'Задача успешно назначена'
    }), 200

@tasks_bp.route('/urgent', methods=['GET'])
@jwt_required()
def get_urgent_tasks():
    """Получить срочные задачи"""
    user_id = get_jwt_identity()
    user = User.query.get_or_404(user_id)
    
    query = Task.query.filter(Task.priority.in_(['urgent', 'high']))
    
    if user.role == 'employee':
        query = query.join(Assignment).filter(Assignment.assigned_to == user_id)
    
    tasks = query.filter(Task.status.in_(['pending', 'assigned', 'in_progress'])).all()
    
    schema = TaskSchema(many=True)
    return jsonify({
        'success': True,
        'data': schema.dump(tasks)
    }), 200

@tasks_bp.route('/queue', methods=['GET'])
@jwt_required()
def get_task_queue():
    """Получить очередь задач для назначения"""
    user_id = get_jwt_identity()
    user = User.query.get_or_404(user_id)
    
    if user.role != 'manager':
        return jsonify({
            'success': False,
            'message': 'Недостаточно прав'
        }), 403
    
    # Задачи без назначения
    tasks = Task.query.filter_by(status='pending').order_by(
        Task.priority.desc(),
        Task.created_at.asc()
    ).all()
    
    schema = TaskSchema(many=True)
    return jsonify({
        'success': True,
        'data': schema.dump(tasks)
    }), 200

@tasks_bp.route('/<int:task_id>/recommendations', methods=['GET'])
@jwt_required()
def get_task_recommendations(task_id):
    """Получить рекомендации ИИ для задачи"""
    task = Task.query.get_or_404(task_id)
    user_id = get_jwt_identity()
    user = User.query.get_or_404(user_id)
    
    if user.role != 'manager':
        return jsonify({
            'success': False,
            'message': 'Недостаточно прав'
        }), 403
    
    from app.services.ai_recommender import find_suitable_employees_for_task
    from app.models import User
    
    employees = User.query.filter_by(role='employee').all()
    suitable = find_suitable_employees_for_task(task, employees)
    
    return jsonify({
        'success': True,
        'data': {
            'task': task.to_dict(),
            'recommended_assignees': [
                {
                    'id': emp.id,
                    'name': emp.name,
                    'position': emp.position,
                    'efficiency_score': emp.efficiency_score,
                    'current_workload': emp.current_workload,
                    'max_workload': emp.max_workload,
                    'workload_percentage': (emp.current_workload / emp.max_workload * 100) if emp.max_workload > 0 else 0
                }
                for emp in suitable[:5]
            ]
        }
    }), 200