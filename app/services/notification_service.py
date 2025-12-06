from datetime import datetime, timedelta
from app.database import db
from app.models import Notification, Task, Assignment

def create_deadline_notifications():
    """Создать уведомления о приближающихся дедлайнах"""
    # Задачи с дедлайном в ближайшие 24 часа
    tomorrow = datetime.utcnow() + timedelta(days=1)
    today = datetime.utcnow()
    
    upcoming_tasks = Task.query.filter(
        Task.deadline.between(today, tomorrow),
        Task.status.in_(['assigned', 'in_progress'])
    ).all()
    
    notifications_created = 0
    
    for task in upcoming_tasks:
        if not task.deadline:
            continue
        
        # Проверяем, не создано ли уже уведомление за последние 6 часов
        hours_until_deadline = (task.deadline - datetime.utcnow()).total_seconds() / 3600
        
        # Создаем уведомления для назначенных сотрудников
        for assignment in task.assignments:
            if assignment.assigned_to and assignment.status in ['assigned', 'in_progress']:
                # Проверяем, нет ли уже такого уведомления
                existing_notification = Notification.query.filter_by(
                    user_id=assignment.assigned_to,
                    type='deadline_approaching',
                    related_task_id=task.id,
                    is_read=False
                ).first()
                
                if not existing_notification:
                    message = f'Дедлайн задачи "{task.title}" через {int(hours_until_deadline)} часов'
                    if hours_until_deadline < 1:
                        message = f'Дедлайн задачи "{task.title}" менее чем через час!'
                    
                    notification = Notification(
                        user_id=assignment.assigned_to,
                        type='deadline_approaching',
                        title='Приближается дедлайн',
                        message=message,
                        related_task_id=task.id,
                        is_read=False
                    )
                    db.session.add(notification)
                    notifications_created += 1
    
    db.session.commit()
    return notifications_created

def create_overdue_notifications():
    """Создать уведомления о просроченных задачах"""
    overdue_tasks = Task.query.filter(
        Task.deadline < datetime.utcnow(),
        Task.status.in_(['assigned', 'in_progress'])
    ).all()
    
    notifications_created = 0
    
    for task in overdue_tasks:
        for assignment in task.assignments:
            if assignment.assigned_to and assignment.status in ['assigned', 'in_progress']:
                # Проверяем, нет ли уже такого уведомления за последние 24 часа
                yesterday = datetime.utcnow() - timedelta(days=1)
                existing_notification = Notification.query.filter(
                    Notification.user_id == assignment.assigned_to,
                    Notification.type == 'task_overdue',
                    Notification.related_task_id == task.id,
                    Notification.created_at > yesterday
                ).first()
                
                if not existing_notification:
                    days_overdue = (datetime.utcnow() - task.deadline).days
                    notification = Notification(
                        user_id=assignment.assigned_to,
                        type='task_overdue',
                        title='Просроченная задача',
                        message=f'Задача "{task.title}" просрочена на {days_overdue} дней',
                        related_task_id=task.id,
                        is_read=False
                    )
                    db.session.add(notification)
                    notifications_created += 1
    
    db.session.commit()
    return notifications_created

