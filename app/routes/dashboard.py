from flask import Blueprint, jsonify
from datetime import datetime
from app.database import db
from app.models import User, Task, Assignment
from sqlalchemy import or_

dashboard_bp = Blueprint('dashboard', __name__)

@dashboard_bp.route('/manager', methods=['GET'])
def manager_dashboard():
    """Дашборд для менеджера"""
    # Без авторизации - просто возвращаем данные
    
    # Статистика
    total_tasks = Task.query.count()
    active_tasks = Task.query.filter(Task.status.in_(['assigned', 'in_progress'])).count()
    overdue_tasks = Task.query.filter(
        Task.deadline < datetime.utcnow(),
        Task.status.in_(['assigned', 'in_progress'])
    ).count()
    completed_tasks = Task.query.filter_by(status='completed').count()
    
    # Пользователи
    total_users = User.query.count()
    employees = User.query.filter_by(role='employee').count()
    managers = User.query.filter_by(role='manager').count()
    
    # Загруженность команды
    employees_list = User.query.filter_by(role='employee').all()
    avg_workload = sum(e.current_workload for e in employees_list) / len(employees_list) if employees_list else 0
    
    # Получаем задачи с назначениями для отображения
    tasks_with_assignments = db.session.query(Task, Assignment, User).outerjoin(
        Assignment, Task.id == Assignment.task_id
    ).outerjoin(
        User, Assignment.assigned_to == User.id
    ).filter(
        or_(Task.status == 'assigned', Task.status == 'in_progress', Task.status == 'completed')
    ).order_by(Task.created_at.desc()).limit(10).all()
    
    tasks_data = []
    for task, assignment, user in tasks_with_assignments:
        task_dict = task.to_dict()
        if assignment and user:
            task_dict['employee'] = user.name
            task_dict['employeeEmail'] = user.email
            task_dict['progress'] = assignment.workload_points or 0
            task_dict['maxProgress'] = user.max_workload or 0
        tasks_data.append(task_dict)
    
    # Загруженность сотрудников
    employee_loads = []
    for emp in employees_list:
        employee_loads.append({
            'name': emp.name,
            'load': emp.current_workload,
            'maxLoad': emp.max_workload
        })
    
    # Рекомендации ИИ
    from app.services.ai_recommendations_service import generate_recommendations
    recommendations = generate_recommendations()
    applied_recommendations = len([r for r in recommendations if r.get('applied', False)])
    
    return jsonify({
        'success': True,
        'data': {
            'stats': {
                'total': total_tasks,
                'active': active_tasks,
                'overdue': overdue_tasks,
                'completed': completed_tasks
            },
            'tasks': tasks_data,
            'employeeLoads': employee_loads,
            'aiAnalysis': {
                'recommendations': len(recommendations),
                'applied': applied_recommendations
            }
        }
    }), 200

@dashboard_bp.route('/employee', methods=['GET'])
def employee_dashboard():
    """Дашборд для сотрудника"""
    # Без авторизации - берем первого сотрудника или возвращаем пустые данные
    user = User.query.filter_by(role='employee').first()
    if not user:
        return jsonify({
            'success': True,
            'data': {
                'user': None,
                'tasks': {
                    'total': 0,
                    'pending': 0,
                    'in_progress': 0,
                    'completed': 0
                },
                'upcoming_deadlines': []
            }
        }), 200
    
    user_id = user.id
    
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

