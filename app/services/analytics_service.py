"""
Сервис аналитики и метрик эффективности
"""
from datetime import datetime, timedelta
from app.database import db
from app.models import User, Task, Assignment, ModelMetrics


def get_team_analytics(days=30):
    """
    Получить аналитику команды за период
    
    Args:
        days: Количество дней для анализа
    
    Returns:
        dict: Словарь с аналитикой
    """
    cutoff_date = datetime.utcnow() - timedelta(days=days)
    
    # Статистика задач
    total_tasks = Task.query.filter(Task.created_at >= cutoff_date).count()
    from sqlalchemy import or_
    active_tasks = Task.query.filter(
        or_(Task.status == 'assigned', Task.status == 'in_progress'),
        Task.created_at >= cutoff_date
    ).count()
    completed_tasks = Task.query.filter(
        Task.status == 'completed',
        Task.created_at >= cutoff_date
    ).count()
    overdue_tasks = Task.query.filter(
        Task.deadline < datetime.utcnow(),
        or_(Task.status == 'assigned', Task.status == 'in_progress'),
        Task.created_at >= cutoff_date
    ).count()
    
    # Средняя загруженность
    employees = User.query.filter_by(role='employee').all()
    avg_load = 0.0
    if employees:
        total_load = sum(e.current_workload for e in employees)
        total_max = sum(e.max_workload for e in employees)
        avg_load = (total_load / total_max * 100) if total_max > 0 else 0.0
    
    # Эффективность команды
    avg_efficiency = 0.0
    if employees:
        avg_efficiency = sum(e.efficiency for e in employees) / len(employees)
    
    return {
        'tasks': {
            'total': total_tasks,
            'active': active_tasks,
            'completed': completed_tasks,
            'overdue': overdue_tasks,
        },
        'workload': {
            'average': round(avg_load, 1),
        },
        'efficiency': {
            'average': round(avg_efficiency, 1),
        },
        'period_days': days,
    }


def get_employee_metrics(user_id, days=30):
    """
    Получить метрики эффективности сотрудника
    
    Args:
        user_id: ID сотрудника
        days: Период анализа в днях
    
    Returns:
        dict: Метрики сотрудника
    """
    user = User.query.get(user_id)
    if not user:
        return None
    
    cutoff_date = datetime.utcnow() - timedelta(days=days)
    
    # Задачи за период
    assignments = Assignment.query.filter(
        Assignment.assigned_to == user_id,
        Assignment.assigned_at >= cutoff_date
    ).all()
    
    completed = [a for a in assignments if a.status == 'completed']
    in_progress = [a for a in assignments if a.status == 'in_progress']
    
    # Количество проектов (упрощенно: уникальные задачи)
    projects = len(set(a.task_id for a in assignments))
    
    return {
        'user_id': user_id,
        'name': user.name,
        'satisfaction': user.satisfaction or 0,
        'efficiency': user.efficiency or 0,
        'projects': projects,
        'avg_hours_per_month': user.avg_hours_per_month or 0,
        'salary': str(user.salary) if user.salary else '0',
        'tasks_completed': len(completed),
        'tasks_in_progress': len(in_progress),
        'current_load_percent': round((user.current_workload / user.max_workload * 100) if user.max_workload > 0 else 0, 1),
    }


def get_model_metrics():
    """Получить метрики ИИ модели"""
    metrics = ModelMetrics.query.first()
    if not metrics:
        # Создаем дефолтные метрики
        metrics = ModelMetrics(
            training_examples=12847,
            accuracy=94.2,
            f1_score=0.91,
            training_time_minutes=8.0
        )
        db.session.add(metrics)
        db.session.commit()
    
    return metrics.to_dict()


def update_model_metrics(training_examples=None, accuracy=None, f1_score=None, training_time_minutes=None):
    """Обновить метрики модели"""
    metrics = ModelMetrics.query.first()
    if not metrics:
        metrics = ModelMetrics()
        db.session.add(metrics)
    
    if training_examples is not None:
        metrics.training_examples = training_examples
    if accuracy is not None:
        metrics.accuracy = accuracy
    if f1_score is not None:
        metrics.f1_score = f1_score
    if training_time_minutes is not None:
        metrics.training_time_minutes = training_time_minutes
    
    metrics.last_training_date = datetime.utcnow()
    metrics.updated_at = datetime.utcnow()
    
    db.session.commit()
    return metrics

