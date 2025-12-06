"""
Сервис анализа предпочтений времени работы
"""
from datetime import datetime, time
from app.database import db
from app.models import User, WorkPreference, Task


def get_work_preference(user_id):
    """Получить предпочтения времени работы пользователя"""
    preference = WorkPreference.query.filter_by(user_id=user_id).first()
    return preference.to_dict() if preference else None


def calculate_time_preference_score(user_id, task_deadline):
    """
    Рассчитать оценку соответствия предпочтениям времени работы
    
    Args:
        user_id: ID пользователя
        task_deadline: Дедлайн задачи (datetime)
    
    Returns:
        float: Оценка (0-1)
    """
    preference = WorkPreference.query.filter_by(user_id=user_id).first()
    if not preference or not task_deadline:
        return 0.5  # Средняя оценка если нет предпочтений
    
    # Простая логика: если дедлайн в рабочее время пользователя - выше оценка
    # В реальной реализации можно учитывать часовой пояс и конкретные дни
    
    # Для упрощения: если дедлайн в будущем и есть предпочтения - даем базовую оценку
    if task_deadline > datetime.utcnow():
        return 0.7  # Хорошая оценка если дедлайн в будущем
    
    return 0.3  # Низкая оценка если дедлайн в прошлом


def is_user_available_at_time(user_id, target_datetime):
    """
    Проверить доступность пользователя в указанное время
    
    Args:
        user_id: ID пользователя
        target_datetime: Целевое время (datetime)
    
    Returns:
        bool: Доступен ли пользователь
    """
    preference = WorkPreference.query.filter_by(user_id=user_id).first()
    if not preference:
        return True  # Если нет предпочтений, считаем доступным
    
    # Простая проверка: если есть предпочтения, проверяем день недели
    if preference.preferred_days:
        days = preference.preferred_days.split(',')
        weekday_names = ['monday', 'tuesday', 'wednesday', 'thursday', 'friday', 'saturday', 'sunday']
        target_weekday = weekday_names[target_datetime.weekday()].lower()
        
        return target_weekday in [d.strip().lower() for d in days]
    
    return True

