from flask import Blueprint, request, jsonify
from datetime import datetime
from app.database import db
from app.models import Task, Assignment, User, TaskHistory, Notification
from app.schemas.task_schema import TaskSchema, CreateTaskSchema
from app.services.task_distributor import assign_task_automatically
from app.services.task_history_service import create_task_history_entry, track_task_update

tasks_bp = Blueprint('tasks', __name__)

@tasks_bp.route('', methods=['GET'])
def get_tasks():
    """Получить список задач"""
    # Без авторизации - показываем все задачи
    # Фильтры
    status = request.args.get('status')
    assigned_to = request.args.get('assigned_to')
    search = request.args.get('search')
    priority = request.args.get('priority')
    
    # Показываем все задачи
    query = Task.query
    if assigned_to:
        query = query.join(Assignment).filter(Assignment.assigned_to == assigned_to)
    
    if status:
        query = query.filter(Task.status == status)
    
    if priority:
        query = query.filter(Task.priority == priority)
    
    if search:
        search_term = f'%{search}%'
        # Поиск по названию, описанию задачи и имени пользователя
        # Используем outerjoin для поиска по имени пользователя, даже если задача не назначена
        query = query.outerjoin(Assignment).outerjoin(User, Assignment.assigned_to == User.id).filter(
            db.or_(
                Task.title.ilike(search_term),
                Task.description.ilike(search_term),
                User.name.ilike(search_term)
            )
        ).distinct()
    
    tasks = query.all()
    
    # Формируем данные с assignments и пользователями
    tasks_data = []
    for task in tasks:
        task_dict = task.to_dict()
        # Добавляем assignments с информацией о пользователях
        assignments_data = []
        for assignment in task.assignments:
            assignment_dict = assignment.to_dict()
            if assignment.assigned_to:
                user = User.query.get(assignment.assigned_to)
                if user:
                    assignment_dict['assigned_to_user'] = user.to_dict()
            assignments_data.append(assignment_dict)
        task_dict['assignments'] = assignments_data
        # Добавляем теги
        task_dict['tags'] = [tag.to_dict() for tag in task.tags]
        tasks_data.append(task_dict)
    
    return jsonify({
        'success': True,
        'data': tasks_data
    }), 200

@tasks_bp.route('', methods=['POST'])
def create_task():
    """Создать задачу"""
    if not request.json:
        return jsonify({
            'success': False,
            'message': 'Отсутствуют данные'
        }), 400
    
    schema = CreateTaskSchema()
    try:
        data = schema.load(request.json)
    except Exception as e:
        return jsonify({
            'success': False,
            'message': 'Ошибка валидации',
            'errors': str(e)
        }), 400
    
    # Без авторизации - берем первого менеджера или создаем от имени системы
    user = User.query.filter_by(role='manager').first()
    user_id = user.id if user else 1
    
    # Парсинг deadline если это строка
    deadline = data.get('deadline')
    if deadline and isinstance(deadline, str):
        try:
            deadline = datetime.fromisoformat(deadline.replace('Z', '+00:00'))
        except (ValueError, AttributeError):
            deadline = None
    
    # Парсинг rating если есть
    rating = data.get('rating')
    
    # Создание задачи
    task = Task(
        title=data['title'],
        description=data.get('description'),
        priority=data.get('priority', 'medium'),
        deadline=deadline,
        estimated_hours=data.get('estimated_hours'),
        rating=rating,
        created_by=user_id
    )
    
    db.session.add(task)
    db.session.flush()
    
    # Создаем запись в истории
    create_task_history_entry(
        task_id=task.id,
        user_id=user_id,
        action='created'
    )
    
    # Автоматическое назначение задачи
    assignment = assign_task_automatically(task.id, user_id)
    
    if assignment:
        task.status = 'assigned'
        # Создаем уведомление для назначенного сотрудника
        if assignment.assigned_to and assignment.assigned_to != user_id:
            notification = Notification(
                user_id=assignment.assigned_to,
                type='task_assigned',
                title='Вам назначена новая задача',
                message=f'Задача "{task.title}" назначена вам',
                related_task_id=task.id,
                is_read=False
            )
            db.session.add(notification)
    
    db.session.commit()
    
    result_schema = TaskSchema()
    return jsonify({
        'success': True,
        'data': result_schema.dump(task),
        'message': 'Задача успешно создана'
    }), 201

@tasks_bp.route('/<int:task_id>', methods=['GET'])
def get_task(task_id):
    """Получить задачу по ID"""
    task = Task.query.get_or_404(task_id)
    
    task_dict = task.to_dict()
    # Добавляем assignments с информацией о пользователях
    assignments_data = []
    for assignment in task.assignments:
        assignment_dict = assignment.to_dict()
        if assignment.assigned_to:
            user = User.query.get(assignment.assigned_to)
            if user:
                assignment_dict['assigned_to_user'] = user.to_dict()
        assignments_data.append(assignment_dict)
    task_dict['assignments'] = assignments_data
    # Добавляем теги
    task_dict['tags'] = [tag.to_dict() for tag in task.tags]
    
    return jsonify({
        'success': True,
        'data': task_dict
    }), 200

@tasks_bp.route('/<int:task_id>', methods=['PUT'])
def update_task(task_id):
    """Обновить задачу"""
    task = Task.query.get_or_404(task_id)
    # Без авторизации - разрешаем все изменения
    
    schema = TaskSchema()
    try:
        data = schema.load(request.json, partial=True)
    except Exception as e:
        return jsonify({
            'success': False,
            'message': 'Ошибка валидации',
            'errors': str(e)
        }), 400
    
    # Сохраняем старые значения для истории
    old_data = {
        'title': task.title,
        'description': task.description,
        'priority': task.priority,
        'status': task.status,
        'deadline': task.deadline.isoformat() if task.deadline else None,
        'estimated_hours': float(task.estimated_hours) if task.estimated_hours else None,
        'rating': task.rating,
    }
    
    # Обновление полей
    new_data = {}
    for key, value in data.items():
        # Сотрудник может изменять только статус и rating
        if user.role == 'employee' and key not in ['status', 'rating']:
            continue
        
        if hasattr(task, key) and key not in ['id', 'created_by', 'created_at', 'updated_at']:
            # Парсинг deadline если это строка
            if key == 'deadline' and isinstance(value, str):
                try:
                    value = datetime.fromisoformat(value.replace('Z', '+00:00'))
                except (ValueError, AttributeError):
                    value = None
            new_data[key] = value
            setattr(task, key, value)
    
    # Отслеживаем изменения
    track_task_update(task, user_id, old_data, new_data)
    
    # Создаем уведомления при изменении статуса
    if 'status' in new_data and old_data['status'] != new_data['status']:
        if new_data['status'] == 'completed':
            # Уведомление создателю задачи
            if task.created_by != user_id:
                notification = Notification(
                    user_id=task.created_by,
                    type='task_completed',
                    title='Задача выполнена',
                    message=f'Задача "{task.title}" выполнена',
                    related_task_id=task_id,
                    is_read=False
                )
                db.session.add(notification)
        elif new_data['status'] == 'in_progress':
            # Уведомление создателю о начале работы
            if task.created_by != user_id:
                notification = Notification(
                    user_id=task.created_by,
                    type='task_started',
                    title='Начата работа над задачей',
                    message=f'Начата работа над задачей "{task.title}"',
                    related_task_id=task_id,
                    is_read=False
                )
                db.session.add(notification)
    
    db.session.commit()
    
    return jsonify({
        'success': True,
        'data': schema.dump(task),
        'message': 'Задача успешно обновлена'
    }), 200

@tasks_bp.route('/<int:task_id>', methods=['DELETE'])
def delete_task(task_id):
    """Удалить задачу"""
    task = Task.query.get_or_404(task_id)
    user = User.query.filter_by(role='manager').first()
    user_id = user.id if user else 1
    
    # Проверка прав
    if task.created_by != user_id:
        user = User.query.get(user_id)
        if user.role != 'manager':
            return jsonify({
                'success': False,
                'message': 'Недостаточно прав'
            }), 403
    
    # Создаем запись в истории перед удалением (если нужно сохранить историю)
    create_task_history_entry(
        task_id=task_id,
        user_id=user_id,
        action='deleted'
    )
    
    db.session.delete(task)
    db.session.commit()
    
    return jsonify({
        'success': True,
        'message': 'Задача успешно удалена'
    }), 200

@tasks_bp.route('/<int:task_id>/assign', methods=['POST'])
def assign_task(task_id):
    """Автоматически назначить задачу"""
    task = Task.query.get_or_404(task_id)
    user = User.query.filter_by(role='manager').first()
    user_id = user.id if user else 1
    
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
    
    old_status = task.status
    task.status = 'assigned'
    
    # Создаем запись в истории
    create_task_history_entry(
        task_id=task_id,
        user_id=user_id,
        action='assigned',
        field_name='status',
        old_value=old_status,
        new_value='assigned'
    )
    
    # Создаем уведомление для назначенного сотрудника
    if assignment.assigned_to and assignment.assigned_to != user_id:
        notification = Notification(
            user_id=assignment.assigned_to,
            type='task_assigned',
            title='Вам назначена новая задача',
            message=f'Задача "{task.title}" назначена вам',
            related_task_id=task_id,
            is_read=False
        )
        db.session.add(notification)
    
    db.session.commit()
    
    return jsonify({
        'success': True,
        'data': assignment.to_dict(),
        'message': 'Задача успешно назначена'
    }), 200

@tasks_bp.route('/<int:task_id>/status', methods=['PUT'])
def update_task_status(task_id):
    """Обновить статус задачи (для сотрудников)"""
    task = Task.query.get_or_404(task_id)
    user = User.query.filter_by(role='manager').first()
    user_id = user.id if user else 1
    user = User.query.get(user_id)
    
    if not request.json or 'status' not in request.json:
        return jsonify({
            'success': False,
            'message': 'Отсутствует статус'
        }), 400
    
    new_status = request.json['status']
    
    # Проверка прав: сотрудник может изменять статус только своих задач
    if user.role == 'employee':
        assignment = Assignment.query.filter_by(task_id=task_id, assigned_to=user_id).first()
        if not assignment:
            return jsonify({
                'success': False,
                'message': 'Недостаточно прав'
            }), 403
    
    old_status = task.status
    task.status = new_status
    
    # Обновляем статус assignment
    assignment = Assignment.query.filter_by(task_id=task_id, assigned_to=user_id).first()
    if assignment:
        assignment.status = new_status
        if new_status == 'completed':
            assignment.completed_at = datetime.utcnow()
    
    # Создаем запись в истории
    create_task_history_entry(
        task_id=task_id,
        user_id=user_id,
        action='status_changed',
        field_name='status',
        old_value=old_status,
        new_value=new_status
    )
    
    # Создаем уведомления
    if new_status == 'completed':
        if task.created_by != user_id:
            notification = Notification(
                user_id=task.created_by,
                type='task_completed',
                title='Задача выполнена',
                message=f'Задача "{task.title}" выполнена',
                related_task_id=task_id,
                is_read=False
            )
            db.session.add(notification)
    elif new_status == 'in_progress':
        if task.created_by != user_id:
            notification = Notification(
                user_id=task.created_by,
                type='task_started',
                title='Начата работа над задачей',
                message=f'Начата работа над задачей "{task.title}"',
                related_task_id=task_id,
                is_read=False
            )
            db.session.add(notification)
    
    db.session.commit()
    
    return jsonify({
        'success': True,
        'data': task.to_dict(),
        'message': 'Статус задачи обновлен'
    }), 200
