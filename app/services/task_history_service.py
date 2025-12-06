from datetime import datetime
from app.database import db
from app.models import TaskHistory, Task, Notification

def create_task_history_entry(task_id, user_id, action, field_name=None, old_value=None, new_value=None):
    """Создать запись в истории изменений задачи"""
    entry = TaskHistory(
        task_id=task_id,
        user_id=user_id,
        action=action,
        field_name=field_name,
        old_value=str(old_value) if old_value is not None else None,
        new_value=str(new_value) if new_value is not None else None
    )
    db.session.add(entry)
    return entry

def track_task_update(task, user_id, old_data, new_data):
    """Отследить изменения задачи и создать записи в истории"""
    # Отслеживаем изменения полей
    fields_to_track = ['title', 'description', 'priority', 'status', 'deadline', 'estimated_hours']
    
    for field in fields_to_track:
        old_val = old_data.get(field)
        new_val = new_data.get(field) if field in new_data else getattr(task, field, None)
        
        if old_val != new_val:
            action = 'updated'
            if field == 'status':
                action = 'status_changed'
            elif field == 'priority':
                action = 'priority_changed'
            elif field == 'deadline':
                action = 'deadline_changed'
            
            create_task_history_entry(
                task_id=task.id,
                user_id=user_id,
                action=action,
                field_name=field,
                old_value=old_val,
                new_value=new_val
            )
            
            # Создаем уведомления для важных изменений
            if field == 'status' and new_val == 'assigned':
                # Уведомление назначенному сотруднику
                for assignment in task.assignments:
                    if assignment.assigned_to and assignment.assigned_to != user_id:
                        notification = Notification(
                            user_id=assignment.assigned_to,
                            type='task_assigned',
                            title='Вам назначена новая задача',
                            message=f'Задача "{task.title}" назначена вам',
                            related_task_id=task.id,
                            is_read=False
                        )
                        db.session.add(notification)
            
            elif field == 'deadline' and new_val:
                # Уведомление о изменении дедлайна
                for assignment in task.assignments:
                    if assignment.assigned_to and assignment.assigned_to != user_id:
                        notification = Notification(
                            user_id=assignment.assigned_to,
                            type='deadline_changed',
                            title='Изменен дедлайн задачи',
                            message=f'Изменен дедлайн задачи "{task.title}"',
                            related_task_id=task.id,
                            is_read=False
                        )
                        db.session.add(notification)

