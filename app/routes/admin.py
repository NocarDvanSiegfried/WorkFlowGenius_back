from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from datetime import datetime, timedelta
from app.database import db
from app.models import User, Task, Assignment
from app.services.task_distributor import assign_task_automatically

admin_bp = Blueprint('admin', __name__)

@admin_bp.route('/create_task', methods=['POST'])
@jwt_required()
def admin_create_task():
    """Создание задачи администратором (с расширенными возможностями)"""
    user_id = get_jwt_identity()
    current_user = User.query.get_or_404(user_id)
    
    # Только менеджеры
    if current_user.role != 'manager':
        return jsonify({
            'success': False,
            'message': 'Недостаточно прав'
        }), 403
    
    data = request.json
    if not data:
        return jsonify({
            'success': False,
            'message': 'Отсутствуют данные'
        }), 400
    
    # Валидация обязательных полей
    if 'title' not in data:
        return jsonify({
            'success': False,
            'message': 'Поле "title" обязательно'
        }), 400
    
    # Создание задачи
    task = Task(
        title=data['title'],
        description=data.get('description'),
        priority=data.get('priority', 'medium'),
        deadline=datetime.fromisoformat(data['deadline'].replace('Z', '+00:00')) if data.get('deadline') else None,
        estimated_hours=data.get('estimated_hours'),
        created_by=user_id,
        status='pending'
    )
    
    db.session.add(task)
    db.session.flush()  # Получаем ID задачи
    
    # Если указан конкретный исполнитель
    if 'assigned_to' in data:
        assigned_to = data['assigned_to']
        target_user = User.query.get(assigned_to)
        
        if not target_user or target_user.role != 'employee':
            return jsonify({
                'success': False,
                'message': 'Некорректный ID исполнителя'
            }), 400
        
        # Проверка загруженности
        if target_user.current_workload >= target_user.max_workload:
            return jsonify({
                'success': False,
                'message': 'Сотрудник перегружен'
            }), 400
        
        # Создание ручного назначения
        assignment = Assignment(
            task_id=task.id,
            assigned_to=assigned_to,
            assigned_by=user_id,
            workload_points=data.get('workload_points', 10),
            status='assigned'
        )
        
        # Обновление загруженности
        target_user.current_workload = min(
            target_user.current_workload + assignment.workload_points,
            target_user.max_workload
        )
        
        task.status = 'assigned'
        db.session.add(assignment)
    
    db.session.commit()
    
    return jsonify({
        'success': True,
        'data': task.to_dict(),
        'message': 'Задача успешно создана'
    }), 201

@admin_bp.route('/ai_settings', methods=['GET'])
@jwt_required()
def get_ai_settings():
    """Получить настройки AI-распределения"""
    user_id = get_jwt_identity()
    current_user = User.query.get_or_404(user_id)
    
    # Только менеджеры
    if current_user.role != 'manager':
        return jsonify({
            'success': False,
            'message': 'Недостаточно прав'
        }), 403
    
    # Статические настройки (в будущем можно хранить в БД)
    return jsonify({
        'success': True,
        'data': {
            'algorithm': 'workload_based',
            'priorities': {
                'urgent': 20,
                'high': 15,
                'medium': 10,
                'low': 5
            },
            'auto_assignment': True,
            'consider_skills': False,  # Будущая функция
            'max_workload_percent': 90,
            'version': '1.0.0'
        }
    }), 200

@admin_bp.route('/analytics', methods=['GET'])
@jwt_required()
def get_analytics():
    """Получить аналитику по системе"""
    user_id = get_jwt_identity()
    current_user = User.query.get_or_404(user_id)
    
    # Только менеджеры
    if current_user.role != 'manager':
        return jsonify({
            'success': False,
            'message': 'Недостаточно прав'
        }), 403
    
    # Временные рамки (последние 30 дней)
    thirty_days_ago = datetime.utcnow() - timedelta(days=30)
    
    # Общая статистика
    total_tasks = Task.query.count()
    total_users = User.query.count()
    total_completed = Task.query.filter_by(status='completed').count()
    
    # Активность за последние 30 дней
    recent_tasks = Task.query.filter(Task.created_at >= thirty_days_ago).count()
    recent_completions = Task.query.filter(
        Task.status == 'completed',
        Task.updated_at >= thirty_days_ago
    ).count()
    
    # Распределение по приоритетам
    priorities = {
        'urgent': Task.query.filter_by(priority='urgent').count(),
        'high': Task.query.filter_by(priority='high').count(),
        'medium': Task.query.filter_by(priority='medium').count(),
        'low': Task.query.filter_by(priority='low').count()
    }
    
    # Самые загруженные сотрудники
    top_employees = User.query.filter_by(role='employee')\
        .order_by(User.current_workload.desc())\
        .limit(5)\
        .all()
    
    # Среднее время выполнения
    completed_tasks_with_dates = Task.query.filter(
        Task.status == 'completed',
        Task.created_at.isnot(None),
        Task.updated_at.isnot(None)
    ).all()
    
    avg_completion_time = 0
    if completed_tasks_with_dates:
        total_hours = sum([
            (task.updated_at - task.created_at).total_seconds() / 3600
            for task in completed_tasks_with_dates
        ])
        avg_completion_time = total_hours / len(completed_tasks_with_dates)
    
    return jsonify({
        'success': True,
        'data': {
            'overall': {
                'total_tasks': total_tasks,
                'total_users': total_users,
                'completion_rate': (total_completed / total_tasks * 100) if total_tasks > 0 else 0
            },
            'recent_activity': {
                'tasks_created': recent_tasks,
                'tasks_completed': recent_completions,
                'period_days': 30
            },
            'priorities': priorities,
            'top_employees': [
                {
                    'id': emp.id,
                    'name': emp.name,
                    'workload': emp.current_workload,
                    'workload_percentage': (emp.current_workload / emp.max_workload * 100) if emp.max_workload > 0 else 0
                }
                for emp in top_employees
            ],
            'performance': {
                'avg_completion_hours': round(avg_completion_time, 2),
                'tasks_per_employee': round(total_tasks / (User.query.filter_by(role='employee').count() or 1), 2)
            }
        }
    }), 200

@admin_bp.route('/teams', methods=['GET'])
@jwt_required()
def get_teams():
    """Получить информацию о командах (группах пользователей)"""
    user_id = get_jwt_identity()
    current_user = User.query.get_or_404(user_id)
    
    # Только менеджеры
    if current_user.role != 'manager':
        return jsonify({
            'success': False,
            'message': 'Недостаточно прав'
        }), 403
    
    # Все сотрудники
    employees = User.query.filter_by(role='employee').all()
    
    # Простая группировка по загруженности
    teams = {
        'low_workload': [],
        'medium_workload': [],
        'high_workload': []
    }
    
    for emp in employees:
        percentage = (emp.current_workload / emp.max_workload * 100) if emp.max_workload > 0 else 0
        
        if percentage < 50:
            teams['low_workload'].append({
                'id': emp.id,
                'name': emp.name,
                'workload_percentage': round(percentage, 1)
            })
        elif percentage < 80:
            teams['medium_workload'].append({
                'id': emp.id,
                'name': emp.name,
                'workload_percentage': round(percentage, 1)
            })
        else:
            teams['high_workload'].append({
                'id': emp.id,
                'name': emp.name,
                'workload_percentage': round(percentage, 1)
            })
    
    return jsonify({
        'success': True,
        'data': {
            'total_employees': len(employees),
            'teams': teams,
            'stats': {
                'average_workload': round(sum(
                    (emp.current_workload / emp.max_workload * 100) if emp.max_workload > 0 else 0
                    for emp in employees
                ) / len(employees) if employees else 0, 2),
                'available_capacity': sum(
                    max(emp.max_workload - emp.current_workload, 0)
                    for emp in employees
                )
            }
        }
    }), 200

@admin_bp.route('/create_teams', methods=['POST'])
@jwt_required()
def create_teams():
    """Автоматическое создание команд на основе компетенций"""
    user_id = get_jwt_identity()
    current_user = User.query.get_or_404(user_id)
    
    # Только менеджеры
    if current_user.role != 'manager':
        return jsonify({
            'success': False,
            'message': 'Недостаточно прав'
        }), 403
    
    data = request.json or {}
    team_count = data.get('team_count', 3)
    
    # Получаем всех сотрудников
    employees = User.query.filter_by(role='employee').all()
    
    if len(employees) < team_count:
        return jsonify({
            'success': False,
            'message': f'Недостаточно сотрудников для создания {team_count} команд'
        }), 400
    
    # Простой алгоритм распределения (можно заменить на более сложный)
    employees_sorted = sorted(employees, key=lambda e: e.current_workload)
    
    teams = []
    for i in range(team_count):
        teams.append({
            'team_id': i + 1,
            'name': f'Команда {i + 1}',
            'members': [],
            'total_workload': 0
        })
    
    # Распределение сотрудников по командам (round-robin)
    for idx, employee in enumerate(employees_sorted):
        team_idx = idx % team_count
        teams[team_idx]['members'].append({
            'id': employee.id,
            'name': employee.name,
            'workload': employee.current_workload
        })
        teams[team_idx]['total_workload'] += employee.current_workload
    
    # Балансировка команд (опционально)
    if data.get('balance', True):
        teams.sort(key=lambda t: t['total_workload'])
    
    return jsonify({
        'success': True,
        'data': {
            'teams': teams,
            'configuration': {
                'team_count': team_count,
                'employees_per_team': round(len(employees) / team_count, 2),
                'algorithm': 'round_robin_balanced'
            }
        },
        'message': f'Создано {team_count} команд'
    }), 200

@admin_bp.route('/system_health', methods=['GET'])
@jwt_required()
def system_health():
    """Проверка здоровья системы (расширенная версия)"""
    user_id = get_jwt_identity()
    current_user = User.query.get_or_404(user_id)
    
    # Только менеджеры
    if current_user.role != 'manager':
        return jsonify({
            'success': False,
            'message': 'Недостаточно прав'
        }), 403
    
    # Проверка подключения к БД
    db_status = 'healthy'
    try:
        db.session.execute('SELECT 1')
    except Exception:
        db_status = 'unhealthy'
    
    # Проверка наличия перегруженных сотрудников
    overloaded_users = User.query.filter(
        User.current_workload >= User.max_workload
    ).count()
    
    # Проверка просроченных задач
    overdue_tasks = Task.query.filter(
        Task.deadline < datetime.utcnow(),
        Task.status.notin_(['completed', 'cancelled'])
    ).count()
    
    # Статистика системы
    total_tasks = Task.query.count()
    active_tasks = Task.query.filter(
        Task.status.in_(['pending', 'assigned', 'in_progress'])
    ).count()
    
    return jsonify({
        'success': True,
        'data': {
            'database': db_status,
            'tasks': {
                'total': total_tasks,
                'active': active_tasks,
                'overdue': overdue_tasks,
                'health_score': round((total_tasks - overdue_tasks) / total_tasks * 100, 2) if total_tasks > 0 else 100
            },
            'users': {
                'total': User.query.count(),
                'overloaded': overloaded_users,
                'available': User.query.filter(
                    User.role == 'employee',
                    User.current_workload < User.max_workload
                ).count()
            },
            'system': {
                'timestamp': datetime.utcnow().isoformat(),
                'uptime': 'N/A',  # Можно добавить мониторинг времени работы
                'memory_usage': 'N/A'  # Для продакшна можно добавить psutil
            }
        }
    }), 200