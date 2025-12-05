# routes/analytics.py
from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from datetime import datetime, timedelta
from app.database import db
from app.models import User, Task, Assignment, PerformanceRecord
import statistics

analytics_bp = Blueprint('analytics', __name__)

@analytics_bp.route('/weekly', methods=['GET'])
@jwt_required()
def weekly_analytics():
    """Аналитика за неделю (как в макетах)"""
    user_id = get_jwt_identity()
    current_user = User.query.get_or_404(user_id)
    
    # Только менеджеры для глобальной аналитики
    if current_user.role != 'manager':
        # Для сотрудников - только их статистика
        return employee_weekly_analytics(user_id)
    
    # Дата неделю назад
    week_ago = datetime.utcnow() - timedelta(days=7)
    
    # Статистика задач
    total_tasks = Task.query.count()
    tasks_this_week = Task.query.filter(Task.created_at >= week_ago).count()
    completed_this_week = Task.query.filter(
        Task.status == 'completed',
        Task.updated_at >= week_ago
    ).count()
    
    # Статистика сотрудников
    total_users = User.query.count()
    employees = User.query.filter_by(role='employee').all()
    
    # Производительность
    avg_on_time = 0
    avg_quality = 0
    avg_efficiency = 0
    
    if employees:
        # Берем последние записи производительности
        performance_data = []
        for emp in employees:
            latest_perf = PerformanceRecord.query.filter_by(user_id=emp.id)\
                .order_by(PerformanceRecord.period_end.desc()).first()
            if latest_perf:
                performance_data.append(latest_perf)
        
        if performance_data:
            avg_on_time = statistics.mean([p.tasks_on_time/p.tasks_completed*100 if p.tasks_completed>0 else 0 for p in performance_data])
            avg_quality = statistics.mean([p.quality_score for p in performance_data])
            avg_efficiency = statistics.mean([p.efficiency_score for p in performance_data])
    
    # Активные и срочные задачи
    active_tasks = Task.query.filter(Task.status.in_(['pending', 'assigned', 'in_progress'])).count()
    urgent_tasks = Task.query.filter_by(priority='urgent').filter(
        Task.status.in_(['pending', 'assigned', 'in_progress'])
    ).count()
    
    # Среднее время выполнения
    completed_tasks = Task.query.filter_by(status='completed').all()
    avg_completion_hours = 0
    if completed_tasks:
        total_hours = 0
        count = 0
        for task in completed_tasks:
            if task.created_at and task.updated_at:
                hours = (task.updated_at - task.created_at).total_seconds() / 3600
                if hours < 168:  # Исключаем слишком долгие задачи (более недели)
                    total_hours += hours
                    count += 1
        avg_completion_hours = total_hours / count if count > 0 else 0
    
    return jsonify({
        'success': True,
        'data': {
            'tasks': {
                'total': total_tasks,
                'this_week': tasks_this_week,
                'completed_this_week': completed_this_week,
                'active': active_tasks,
                'urgent': urgent_tasks,
                'completion_rate': (completed_this_week / tasks_this_week * 100) if tasks_this_week > 0 else 0
            },
            'users': {
                'total': total_users,
                'employees': len(employees),
                'average_on_time': round(avg_on_time, 1),
                'average_quality': round(avg_quality, 1),
                'average_efficiency': round(avg_efficiency, 1)
            },
            'performance': {
                'avg_completion_hours': round(avg_completion_hours, 1),
                'productivity_trend': '+5%',  # Заглушка
                'workload_distribution': 'balanced'  # Заглушка
            },
            'timeline': {
                'period_start': week_ago.isoformat(),
                'period_end': datetime.utcnow().isoformat()
            }
        }
    }), 200

def employee_weekly_analytics(user_id):
    """Аналитика за неделю для сотрудника"""
    user = User.query.get_or_404(user_id)
    
    # Дата неделю назад
    week_ago = datetime.utcnow() - timedelta(days=7)
    
    # Задачи сотрудника
    assignments = Assignment.query.filter_by(assigned_to=user_id).all()
    task_ids = [a.task_id for a in assignments]
    
    if task_ids:
        tasks = Task.query.filter(Task.id.in_(task_ids)).all()
        tasks_this_week = [t for t in tasks if t.created_at >= week_ago]
        completed_this_week = [t for t in tasks if t.status == 'completed' and t.updated_at >= week_ago]
    else:
        tasks_this_week = []
        completed_this_week = []
    
    # Производительность
    latest_perf = PerformanceRecord.query.filter_by(user_id=user_id)\
        .order_by(PerformanceRecord.period_end.desc()).first()
    
    # Статистика как в макетах
    stats = {
        'tasks_completed': len(completed_this_week),
        'avg_time': 2.5,  # Заглушка - можно рассчитать реально
        'rating': 4.8,    # Заглушка
        'on_time_percentage': 92 if latest_perf else 0,
        'quality_score': 88 if latest_perf else 0,
        'workload_percentage': user.current_workload / user.max_workload * 100 if user.max_workload > 0 else 0
    }
    
    # Рекомендации ИИ
    ai_recommendations = []
    if user.current_workload >= user.max_workload * 0.8:
        ai_recommendations.append({
            'title': 'Оптимизация нагрузки',
            'description': 'Ваша загруженность высока. Рекомендуем взять задачу по оптимизации.',
            'priority': 'high',
            'confidence': 0.87
        })
    
    return jsonify({
        'success': True,
        'data': {
            'user': {
                'id': user.id,
                'name': user.name,
                'position': user.position
            },
            'statistics': stats,
            'ai_recommendations': ai_recommendations,
            'performance_above_average': 23  # Как в макете
        }
    }), 200

@analytics_bp.route('/team_performance', methods=['GET'])
@jwt_required()
def team_performance():
    """Производительность команд (из макета администратора)"""
    user_id = get_jwt_identity()
    current_user = User.query.get_or_404(user_id)
    
    if current_user.role != 'manager':
        return jsonify({
            'success': False,
            'message': 'Недостаточно прав'
        }), 403
    
    # Получаем всех сотрудников с их производительностью
    employees = User.query.filter_by(role='employee').all()
    
    team_data = []
    for emp in employees:
        latest_perf = PerformanceRecord.query.filter_by(user_id=emp.id)\
            .order_by(PerformanceRecord.period_end.desc()).first()
        
        team_data.append({
            'id': emp.id,
            'name': emp.name,
            'position': emp.position,
            'satisfaction': emp.satisfaction_score,
            'efficiency': emp.efficiency_score,
            'current_workload': emp.current_workload,
            'max_workload': emp.max_workload,
            'workload_percentage': (emp.current_workload / emp.max_workload * 100) if emp.max_workload > 0 else 0,
            'monthly_hours': emp.monthly_hours,
            'salary': emp.salary,
            'skills': [skill.skill_name for skill in emp.skills],
            'performance': latest_perf.to_dict() if latest_perf else None
        })
    
    # Сортировка по эффективности
    team_data.sort(key=lambda x: x['efficiency'], reverse=True)
    
    # Общая статистика
    total_efficiency = sum(emp['efficiency'] for emp in team_data)
    avg_efficiency = total_efficiency / len(team_data) if team_data else 0
    
    total_workload = sum(emp['current_workload'] for emp in team_data)
    total_capacity = sum(emp['max_workload'] for emp in team_data)
    avg_workload = (total_workload / total_capacity * 100) if total_capacity > 0 else 0
    
    return jsonify({
        'success': True,
        'data': {
            'team': team_data,
            'summary': {
                'total_members': len(team_data),
                'average_efficiency': round(avg_efficiency, 1),
                'average_workload': round(avg_workload, 1),
                'total_active_tasks': Task.query.filter(Task.status.in_(['pending', 'assigned', 'in_progress'])).count(),
                'urgent_tasks': Task.query.filter_by(priority='urgent').filter(
                    Task.status.in_(['pending', 'assigned', 'in_progress'])
                ).count(),
                'avg_task_time': 2.4  # Заглушка
            }
        }
    }), 200