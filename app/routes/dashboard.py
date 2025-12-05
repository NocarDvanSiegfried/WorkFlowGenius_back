# routes/dashboard.py - ОБНОВЛЕННАЯ ВЕРСИЯ
from flask import Blueprint, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from app.database import db
from app.models import User, Task, Assignment, PerformanceRecord, AIRecommendation
from app.services.performance_calculator import calculate_performance
from datetime import datetime, timedelta

dashboard_bp = Blueprint('dashboard', __name__)

@dashboard_bp.route('/manager', methods=['GET'])
@jwt_required()
def manager_dashboard():
    """Дашборд для менеджера - ОБНОВЛЕННЫЙ"""
    user_id = get_jwt_identity()
    user = User.query.get_or_404(user_id)
    
    if user.role != 'manager':
        return jsonify({
            'success': False,
            'message': 'Недостаточно прав'
        }), 403
    
    # Статистика задач
    total_tasks = Task.query.count()
    pending_tasks = Task.query.filter_by(status='pending').count()
    in_progress_tasks = Task.query.filter_by(status='in_progress').count()
    completed_tasks = Task.query.filter_by(status='completed').count()
    urgent_tasks = Task.query.filter_by(priority='urgent').filter(
        Task.status.in_(['pending', 'assigned', 'in_progress'])
    ).count()
    
    # Пользователи
    total_users = User.query.count()
    employees = User.query.filter_by(role='employee').count()
    managers = User.query.filter_by(role='manager').count()
    
    # Загруженность команды
    employees_list = User.query.filter_by(role='employee').all()
    avg_workload = sum(e.current_workload for e in employees_list) / len(employees_list) if employees_list else 0
    avg_efficiency = sum(e.efficiency_score for e in employees_list) / len(employees_list) if employees_list else 0
    avg_satisfaction = sum(e.satisfaction_score for e in employees_list) / len(employees_list) if employees_list else 0
    
    # Рекомендации ИИ для менеджера
    ai_recommendations = AIRecommendation.query.filter_by(status='pending')\
        .order_by(AIRecommendation.priority.desc())\
        .limit(5)\
        .all()
    
    # Активность за последнюю неделю
    week_ago = datetime.utcnow() - timedelta(days=7)
    tasks_this_week = Task.query.filter(Task.created_at >= week_ago).count()
    completed_this_week = Task.query.filter(
        Task.status == 'completed',
        Task.updated_at >= week_ago
    ).count()
    
    return jsonify({
        'success': True,
        'data': {
            'summary': {
                'tasks': {
                    'total': total_tasks,
                    'pending': pending_tasks,
                    'in_progress': in_progress_tasks,
                    'completed': completed_tasks,
                    'urgent': urgent_tasks,
                    'completion_rate': (completed_tasks / total_tasks * 100) if total_tasks > 0 else 0
                },
                'users': {
                    'total': total_users,
                    'employees': employees,
                    'managers': managers,
                    'avg_efficiency': round(avg_efficiency, 1),
                    'avg_satisfaction': round(avg_satisfaction, 1)
                },
                'workload': {
                    'average': round(avg_workload, 2),
                    'optimal_level': 70,
                    'overloaded_count': len([e for e in employees_list if e.current_workload >= e.max_workload * 0.9])
                },
                'weekly_activity': {
                    'tasks_created': tasks_this_week,
                    'tasks_completed': completed_this_week,
                    'completion_rate_weekly': (completed_this_week / tasks_this_week * 100) if tasks_this_week > 0 else 0
                }
            },
            'ai_recommendations': [rec.to_dict() for rec in ai_recommendations],
            'top_performers': [
                {
                    'id': emp.id,
                    'name': emp.name,
                    'email': emp.email,
                    'position': emp.position,
                    'efficiency_score': emp.efficiency_score,
                    'satisfaction_score': emp.satisfaction_score,
                    'current_workload': emp.current_workload,
                    'max_workload': emp.max_workload,
                    'workload_percentage': (emp.current_workload / emp.max_workload * 100) if emp.max_workload > 0 else 0
                }
                for emp in sorted(
                    employees_list,
                    key=lambda x: x.efficiency_score,
                    reverse=True
                )[:3]
            ],
            'urgent_actions': {
                'overdue_tasks': Task.query.filter(
                    Task.deadline < datetime.utcnow(),
                    Task.status.in_(['pending', 'assigned', 'in_progress'])
                ).count(),
                'unassigned_tasks': Task.query.filter_by(status='pending').count(),
                'high_priority_tasks': Task.query.filter_by(priority='urgent').filter(
                    Task.status.in_(['pending', 'assigned'])
                ).count()
            }
        }
    }), 200

@dashboard_bp.route('/employee', methods=['GET'])
@jwt_required()
def employee_dashboard():
    """Дашборд для сотрудника - ОБНОВЛЕННЫЙ"""
    user_id = get_jwt_identity()
    user = User.query.get_or_404(user_id)
    
    # Рассчитать текущую производительность
    performance = calculate_performance(user_id)
    
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
            days_left = (t.deadline - datetime.utcnow()).days
            task_dict = t.to_dict()
            task_dict['days_left'] = days_left
            task_dict['is_urgent'] = days_left <= 2
            upcoming_deadlines.append(task_dict)
    
    # Сортировка по дедлайну (сначала ближайшие)
    upcoming_deadlines.sort(key=lambda x: x['deadline'] if x['deadline'] else '9999-12-31T23:59:59')
    
    # Рекомендации ИИ для сотрудника
    ai_recommendations = AIRecommendation.query.filter_by(
        user_id=user_id,
        status='pending'
    ).order_by(
        AIRecommendation.priority.desc(),
        AIRecommendation.confidence_score.desc()
    ).limit(3).all()
    
    # Статистика как в макетах
    stats = {
        'tasks_completed_week': performance['tasks_completed'],
        'avg_time_per_task': round(performance['total_hours'] / performance['tasks_completed'], 1) if performance['tasks_completed'] > 0 else 0,
        'rating': round(performance['rating'], 1),
        'on_time_percentage': round(performance['on_time_percentage'], 1),
        'quality_score': round(performance['quality_score'], 1),
        'workload_percentage': round(user.current_workload / user.max_workload * 100, 1) if user.max_workload > 0 else 0,
        'efficiency_score': user.efficiency_score,
        'satisfaction_score': user.satisfaction_score
    }
    
    # Производительность выше среднего (как в макете)
    # Здесь можно добавить сравнение с другими сотрудниками
    performance_above_average = 23  # Заглушка
    
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
            'upcoming_deadlines': upcoming_deadlines[:5],
            'performance_stats': stats,
            'ai_recommendations': [rec.to_dict() for rec in ai_recommendations],
            'performance_above_average': performance_above_average,
            'weekly_summary': {
                'period_start': performance['period_start'].isoformat(),
                'period_end': performance['period_end'].isoformat(),
                'hours_worked': round(performance['total_hours'], 1),
                'tasks_per_hour': round(performance['tasks_completed'] / performance['total_hours'], 2) if performance['total_hours'] > 0 else 0
            }
        }
    }), 200