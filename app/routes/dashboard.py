from flask import Blueprint, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from app.database import db
from app.models import User, Task, Assignment

dashboard_bp = Blueprint('dashboard', __name__)

@dashboard_bp.route('/manager', methods=['GET'])
@jwt_required()
def manager_dashboard():
    """Дашборд для менеджера"""
    user_id = get_jwt_identity()
    user = User.query.get_or_404(user_id)
    
    if user.role != 'manager':
        return jsonify({
            'success': False,
            'message': 'Недостаточно прав'
        }), 403
    
    # Статистика
    total_tasks = Task.query.count()
    pending_tasks = Task.query.filter_by(status='pending').count()
    in_progress_tasks = Task.query.filter_by(status='in_progress').count()
    completed_tasks = Task.query.filter_by(status='completed').count()
    
    # Пользователи
    total_users = User.query.count()
    employees = User.query.filter_by(role='employee').count()
    managers = User.query.filter_by(role='manager').count()
    
    # Загруженность команды
    employees_list = User.query.filter_by(role='employee').all()
    avg_workload = sum(e.current_workload for e in employees_list) / len(employees_list) if employees_list else 0
    
    return jsonify({
        'success': True,
        'data': {
            'tasks': {
                'total': total_tasks,
                'pending': pending_tasks,
                'in_progress': in_progress_tasks,
                'completed': completed_tasks
            },
            'users': {
                'total': total_users,
                'employees': employees,
                'managers': managers
            },
            'workload': {
                'average': round(avg_workload, 2),
                'employees': [e.to_dict() for e in employees_list]
            }
        }
    }), 200

@dashboard_bp.route('/employee', methods=['GET'])
@jwt_required()
def employee_dashboard():
    """Дашборд для сотрудника"""
    user_id = get_jwt_identity()
    user = User.query.get_or_404(user_id)
    
    # Мои задачи
    my_assignments = Assignment.query.filter_by(assigned_to=user_id).all()
    my_tasks = [assignment.task for assignment in my_assignments]
    
    # Статистика по моим задачам
    pending = len([t for t in my_tasks if t.status == 'pending' or t.status == 'assigned'])
    in_progress = len([t for t in my_tasks if t.status == 'in_progress'])
    completed = len([t for t in my_tasks if t.status == 'completed'])
    
    # Ближайшие дедлайны
    upcoming_deadlines = []
    for t in my_tasks:
        if t.deadline and t.status not in ['completed', 'cancelled']:
            task_dict = t.to_dict()
            upcoming_deadlines.append(task_dict)
    
    # Сортировка по дедлайну (сначала ближайшие)
    upcoming_deadlines.sort(key=lambda x: x['deadline'] if x['deadline'] else '9999-12-31T23:59:59')
    
    return jsonify({
        'success': True,
        'data': {
            'user': user.to_dict(),
            'tasks': {
                'total': len(my_tasks),
                'pending': pending,
                'in_progress': in_progress,
                'completed': completed
            },
            'upcoming_deadlines': upcoming_deadlines[:5]  # Ближайшие 5
        }
    }), 200

