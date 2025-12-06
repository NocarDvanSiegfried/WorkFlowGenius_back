"""
Сервис анализа загруженности сотрудников
"""
from datetime import datetime, timedelta
from app.database import db
from app.models import User, Assignment, Task


def calculate_current_load(user_id):
    """
    Рассчитать текущую загруженность пользователя
    
    Returns:
        float: Загруженность в процентах (0-100)
    """
    user = User.query.get(user_id)
    if not user or user.max_workload == 0:
        return 0.0
    
    return (user.current_workload / user.max_workload) * 100.0


def get_available_capacity(user_id):
    """
    Получить доступную емкость пользователя
    
    Returns:
        int: Доступные workload_points
    """
    user = User.query.get(user_id)
    if not user:
        return 0
    
    return max(0, user.max_workload - user.current_workload)


def calculate_load_score(user_id):
    """
    Рассчитать оценку загруженности для распределения задач
    Меньше загруженность = выше оценка
    
    Returns:
        float: Оценка (0-1), где 1 = минимальная загруженность
    """
    load_percent = calculate_current_load(user_id)
    
    # Инвертируем: чем меньше загруженность, тем выше оценка
    # 0% загруженности = 1.0, 100% загруженности = 0.0
    return max(0.0, 1.0 - (load_percent / 100.0))


def get_active_assignments_count(user_id):
    """Получить количество активных назначений"""
    from sqlalchemy import or_
    return Assignment.query.filter(
        Assignment.assigned_to == user_id,
        or_(Assignment.status == 'assigned', Assignment.status == 'in_progress')
    ).count()


def get_completed_tasks_count(user_id, days=30):
    """Получить количество выполненных задач за период"""
    cutoff_date = datetime.utcnow() - timedelta(days=days)
    return Assignment.query.filter_by(
        assigned_to=user_id,
        status='completed'
    ).filter(Assignment.completed_at >= cutoff_date).count()

