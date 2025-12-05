# services/performance_calculator.py
from app.database import db
from app.models import User, Task, Assignment, PerformanceRecord
from datetime import datetime, timedelta

def calculate_performance(user_id, period_days=7):
    """Рассчитать производительность пользователя за период"""
    user = User.query.get_or_404(user_id)
    
    # Определяем период
    period_end = datetime.utcnow()
    period_start = period_end - timedelta(days=period_days)
    
    # Получаем задания за период
    assignments = Assignment.query.filter(
        Assignment.assigned_to == user_id,
        Assignment.assigned_at >= period_start
    ).all()
    
    # Статистика
    total_tasks = len(assignments)
    completed_tasks = len([a for a in assignments if a.status == 'completed'])
    
    # Задачи выполненные в срок
    tasks_on_time = 0
    total_hours = 0
    
    for assignment in assignments:
        if assignment.status == 'completed' and assignment.completed_at:
            task = Task.query.get(assignment.task_id)
            if task and task.deadline:
                # Проверка выполнения в срок
                if assignment.completed_at <= task.deadline:
                    tasks_on_time += 1
            
            # Время выполнения
            if assignment.assigned_at and assignment.completed_at:
                hours = (assignment.completed_at - assignment.assigned_at).total_seconds() / 3600
                total_hours += hours
    
    # Рассчитываем метрики
    on_time_percentage = (tasks_on_time / completed_tasks * 100) if completed_tasks > 0 else 0
    
    # Качество (упрощённо - можно добавить ревью оценок)
    quality_score = min(100, on_time_percentage * 1.2) if on_time_percentage > 0 else 0
    
    # Эффективность (задачи в час)
    efficiency_score = 0
    if total_hours > 0:
        tasks_per_hour = completed_tasks / total_hours
        efficiency_score = min(100, tasks_per_hour * 10)  # Нормализация
    
    # Загруженность
    workload_percentage = (user.current_workload / user.max_workload * 100) if user.max_workload > 0 else 0
    
    # Рейтинг (среднее)
    rating = (quality_score/100 * 2.5) + (efficiency_score/100 * 2.5)  # 0-5
    
    # Создаём или обновляем запись производительности
    existing_record = PerformanceRecord.query.filter_by(
        user_id=user_id,
        period_start=period_start.date(),
        period_end=period_end.date()
    ).first()
    
    if existing_record:
        existing_record.tasks_completed = completed_tasks
        existing_record.tasks_on_time = tasks_on_time
        existing_record.total_hours = total_hours
        existing_record.quality_score = quality_score
        existing_record.efficiency_score = efficiency_score
        existing_record.workload_percentage = workload_percentage
        existing_record.rating = rating
    else:
        record = PerformanceRecord(
            user_id=user_id,
            period_start=period_start.date(),
            period_end=period_end.date(),
            tasks_completed=completed_tasks,
            tasks_on_time=tasks_on_time,
            total_hours=total_hours,
            quality_score=quality_score,
            efficiency_score=efficiency_score,
            workload_percentage=workload_percentage,
            rating=rating
        )
        db.session.add(record)
    
    db.session.commit()
    
    return {
        'period_start': period_start,
        'period_end': period_end,
        'tasks_completed': completed_tasks,
        'tasks_on_time': tasks_on_time,
        'on_time_percentage': on_time_percentage,
        'total_hours': total_hours,
        'quality_score': quality_score,
        'efficiency_score': efficiency_score,
        'workload_percentage': workload_percentage,
        'rating': rating
    }

def update_all_performance_records():
    """Обновить записи производительности для всех пользователей"""
    users = User.query.filter_by(role='employee').all()
    
    results = []
    for user in users:
        try:
            performance = calculate_performance(user.id)
            results.append({
                'user_id': user.id,
                'user_name': user.name,
                'performance': performance
            })
        except Exception as e:
            print(f"Error calculating performance for user {user.id}: {e}")
    
    return results