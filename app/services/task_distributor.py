from app.database import db
from app.models import User, Task, Assignment

def assign_task_automatically(task_id, assigned_by):
    """
    Автоматически назначить задачу сотруднику
    
    Простой алгоритм:
    1. Найти всех доступных сотрудников (загруженность < максимума)
    2. Выбрать сотрудника с минимальной загруженностью
    3. Создать назначение
    4. Обновить загруженность сотрудника
    """
    task = Task.query.get(task_id)
    if not task:
        return None
    
    # Проверка: задача уже назначена?
    existing_assignment = Assignment.query.filter_by(task_id=task_id, status='assigned').first()
    if existing_assignment:
        return existing_assignment
    
    # Получить доступных сотрудников
    available_users = User.query.filter(
        User.role == 'employee',
        User.current_workload < User.max_workload
    ).order_by(User.current_workload.asc()).all()
    
    if not available_users:
        return None
    
    # Выбрать сотрудника с минимальной загруженностью
    selected_user = available_users[0]
    
    # Рассчитать workload_points (можно улучшить)
    workload_points = 10
    if task.priority == 'urgent':
        workload_points = 20
    elif task.priority == 'high':
        workload_points = 15
    elif task.priority == 'low':
        workload_points = 5
    
    # Создать назначение
    assignment = Assignment(
        task_id=task_id,
        assigned_to=selected_user.id,
        assigned_by=assigned_by,
        workload_points=workload_points,
        status='assigned'
    )
    
    # Обновить загруженность сотрудника
    selected_user.current_workload = min(
        selected_user.current_workload + workload_points,
        selected_user.max_workload
    )
    
    db.session.add(assignment)
    db.session.commit()
    
    return assignment

