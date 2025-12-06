from app.database import db
from app.models import User, Task, Assignment, AISettings
from app.services.competence_analyzer import calculate_competence_match, get_competence_score
from app.services.workload_analyzer import calculate_load_score, get_available_capacity
from app.services.time_preference_analyzer import calculate_time_preference_score


def get_ai_settings():
    """Получить настройки ИИ (или создать дефолтные)"""
    settings = AISettings.query.first()
    if not settings:
        settings = AISettings()
        db.session.add(settings)
        db.session.commit()
    return settings


def calculate_suitability_score(user, task, ai_settings):
    """
    Рассчитать общую оценку пригодности пользователя для задачи
    
    Args:
        user: Объект User
        task: Объект Task
        ai_settings: Объект AISettings
    
    Returns:
        float: Оценка пригодности (0-1)
    """
    scores = []
    weights = []
    
    # 1. Оценка компетенций
    competence_score = calculate_competence_match(user.id, task.description or task.title)
    scores.append(competence_score)
    weights.append(ai_settings.competence_weight / 100.0)
    
    # 2. Оценка загруженности
    load_score = calculate_load_score(user.id)
    scores.append(load_score)
    weights.append(ai_settings.load_weight / 100.0)
    
    # 3. Оценка предпочтений времени работы
    time_score = calculate_time_preference_score(user.id, task.deadline)
    scores.append(time_score)
    weights.append(ai_settings.time_preference_weight / 100.0)
    
    # 4. Оценка по приоритету (если задача срочная, предпочитаем менее загруженных)
    priority_score = 1.0
    if task.priority == 'urgent':
        # Для срочных задач важнее доступность
        priority_score = load_score
    elif task.priority == 'high':
        priority_score = 0.7 + 0.3 * load_score
    else:
        priority_score = 0.5 + 0.5 * load_score
    
    scores.append(priority_score)
    weights.append(ai_settings.priority_weight / 100.0)
    
    # Взвешенная сумма
    total_weight = sum(weights)
    if total_weight == 0:
        return 0.5
    
    weighted_sum = sum(score * weight for score, weight in zip(scores, weights))
    final_score = weighted_sum / total_weight
    
    return min(max(final_score, 0.0), 1.0)


def assign_task_automatically(task_id, assigned_by):
    """
    Автоматически назначить задачу сотруднику с учетом ИИ-анализа
    
    Улучшенный алгоритм:
    1. Получить настройки ИИ
    2. Найти всех доступных сотрудников
    3. Для каждого рассчитать оценку пригодности (suitability score)
    4. Выбрать сотрудника с максимальной оценкой
    5. Создать назначение с сохранением оценки
    6. Обновить загруженность сотрудника
    """
    task = Task.query.get(task_id)
    if not task:
        return None
    
    # Проверка: задача уже назначена?
    from sqlalchemy import or_
    existing_assignment = Assignment.query.filter(
        Assignment.task_id == task_id,
        or_(Assignment.status == 'assigned', Assignment.status == 'in_progress')
    ).first()
    if existing_assignment:
        return existing_assignment
    
    # Получить настройки ИИ
    ai_settings = get_ai_settings()
    
    # Получить доступных сотрудников
    available_users = User.query.filter(
        User.role == 'employee',
        User.current_workload < User.max_workload
    ).all()
    
    if not available_users:
        return None
    
    # Рассчитать оценки пригодности для каждого сотрудника
    user_scores = []
    for user in available_users:
        suitability_score = calculate_suitability_score(user, task, ai_settings)
        user_scores.append({
            'user': user,
            'score': suitability_score
        })
    
    # Сортировка по оценке (от большего к меньшему)
    user_scores.sort(key=lambda x: x['score'], reverse=True)
    
    # Выбрать лучшего сотрудника
    selected_data = user_scores[0]
    selected_user = selected_data['user']
    suitability_score = selected_data['score']
    
    # Рассчитать workload_points на основе приоритета
    workload_points = 10
    if task.priority == 'urgent':
        workload_points = 20
    elif task.priority == 'high':
        workload_points = 15
    elif task.priority == 'low':
        workload_points = 5
    
    # Проверка доступной емкости
    available_capacity = get_available_capacity(selected_user.id)
    if available_capacity < workload_points:
        # Если недостаточно места, уменьшаем workload_points
        workload_points = available_capacity
    
    if workload_points <= 0:
        return None
    
    # Создать назначение
    assignment = Assignment(
        task_id=task_id,
        assigned_to=selected_user.id,
        assigned_by=assigned_by,
        workload_points=workload_points,
        status='assigned',
        suitability_score=suitability_score
    )
    
    # Обновить загруженность сотрудника
    selected_user.current_workload = min(
        selected_user.current_workload + workload_points,
        selected_user.max_workload
    )
    
    db.session.add(assignment)
    db.session.commit()
    
    return assignment

