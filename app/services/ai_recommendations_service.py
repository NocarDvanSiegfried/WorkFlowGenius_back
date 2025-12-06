"""
Сервис для генерации рекомендаций ИИ
"""
from datetime import datetime, timedelta
from app.database import db
from app.models import User, Task, Assignment
from app.services.analytics_service import get_employee_metrics
from app.services.competence_analyzer import get_competence_score


def generate_recommendations():
    """
    Генерирует рекомендации ИИ на основе анализа текущего состояния
    
    Returns:
        list: Список рекомендаций
    """
    recommendations = []
    
    # 1. Анализ перегрузки сотрудников
    employees = User.query.filter_by(role='employee').all()
    overloaded = []
    underloaded = []
    
    for emp in employees:
        load_percent = (emp.current_workload / emp.max_workload * 100) if emp.max_workload > 0 else 0
        if load_percent > 90:
            overloaded.append(emp)
        elif load_percent < 50:
            underloaded.append(emp)
    
    # Рекомендация по перераспределению задач
    if overloaded and underloaded:
        overloaded_names = ', '.join([e.name for e in overloaded[:3]])
        underloaded_names = ', '.join([e.name for e in underloaded[:3]])
        recommendations.append({
            'id': 'redistribute_tasks',
            'title': 'Перераспределить задачи между сотрудниками',
            'description': f'{overloaded_names} перегружены. Рекомендуется передать часть задач {underloaded_names}',
            'priority': 'high',
            'applied': False,
            'type': 'redistribution',
            'action_data': {
                'overloaded': [e.id for e in overloaded],
                'underloaded': [e.id for e in underloaded]
            }
        })
    
    # 2. Анализ просроченных задач
    overdue_tasks = Task.query.filter(
        Task.deadline < datetime.utcnow(),
        Task.status.in_(['assigned', 'in_progress'])
    ).all()
    
    if overdue_tasks:
        recommendations.append({
            'id': 'extend_deadlines',
            'title': 'Оптимизировать сроки выполнения',
            'description': f'Обнаружено {len(overdue_tasks)} просроченных задач. Рекомендуется пересмотреть сроки или перераспределить ресурсы',
            'priority': 'high',
            'applied': False,
            'type': 'deadline_optimization',
            'action_data': {
                'overdue_count': len(overdue_tasks)
            }
        })
    
    # 3. Рекомендации по добавлению ресурсов
    total_active_tasks = Task.query.filter(
        Task.status.in_(['assigned', 'in_progress'])
    ).count()
    
    available_capacity = sum(
        max(0, e.max_workload - e.current_workload) for e in employees
    )
    
    if total_active_tasks > available_capacity * 0.8:
        recommendations.append({
            'id': 'add_resources',
            'title': 'Добавить дополнительные ресурсы',
            'description': f'Текущая загрузка команды близка к максимуму. Рекомендуется привлечь дополнительных сотрудников',
            'priority': 'medium',
            'applied': False,
            'type': 'resource_management',
            'action_data': {
                'current_load': round((total_active_tasks / (available_capacity + total_active_tasks) * 100), 1) if (available_capacity + total_active_tasks) > 0 else 0
            }
        })
    
    # 4. Рекомендации по компетенциям
    unassigned_tasks = Task.query.filter_by(status='pending').all()
    if unassigned_tasks:
        for task in unassigned_tasks[:5]:  # Проверяем первые 5
            best_match = None
            best_score = 0
            
            for emp in employees:
                if emp.current_workload < emp.max_workload:
                    # Получаем компетенции пользователя
                    from app.models import UserCompetency
                    user_competencies = UserCompetency.query.filter_by(user_id=emp.id).all()
                    user_skills = [c.skill_name for c in user_competencies]
                    
                    # Используем описание задачи для анализа компетенций
                    required_skills = []
                    if task.description:
                        # Простая логика: извлекаем навыки из описания
                        # В реальной системе здесь может быть более сложный анализ
                        description_lower = task.description.lower()
                        common_skills = ['python', 'javascript', 'react', 'node', 'sql', 'api', 'design', 'ui', 'ux']
                        required_skills = [skill for skill in common_skills if skill in description_lower]
                    
                    score = get_competence_score(emp.id, required_skills)
                    if score > best_score:
                        best_score = score
                        best_match = emp
            
            if best_match and best_score > 0.7:
                recommendations.append({
                    'id': f'assign_task_{task.id}',
                    'title': f'Назначить задачу "{task.title}"',
                    'description': f'Задача идеально подходит для {best_match.name} (совпадение компетенций: {int(best_score * 100)}%)',
                    'priority': 'medium',
                    'applied': False,
                    'type': 'task_assignment',
                    'action_data': {
                        'task_id': task.id,
                        'user_id': best_match.id,
                        'match_score': best_score
                    }
                })
    
    # 5. Рекомендации по оптимизации времени
    tasks_with_deadlines = Task.query.filter(
        Task.deadline.isnot(None),
        Task.status.in_(['assigned', 'in_progress'])
    ).all()
    
    if tasks_with_deadlines:
        tight_deadlines = [
            t for t in tasks_with_deadlines
            if t.deadline and (t.deadline - datetime.utcnow()).days < 3
        ]
        
        if tight_deadlines:
            recommendations.append({
                'id': 'optimize_tight_deadlines',
                'title': 'Пересмотреть срочные дедлайны',
                'description': f'Обнаружено {len(tight_deadlines)} задач с дедлайном менее 3 дней. Рекомендуется пересмотреть приоритеты',
                'priority': 'medium',
                'applied': False,
                'type': 'deadline_review',
                'action_data': {
                    'tight_deadlines_count': len(tight_deadlines)
                }
            })
    
    return recommendations


def apply_recommendation(recommendation_id, action_data=None):
    """
    Применить рекомендацию
    
    Args:
        recommendation_id: ID рекомендации
        action_data: Дополнительные данные для применения
    
    Returns:
        bool: Успешно ли применена рекомендация
    """
    recommendations = generate_recommendations()
    recommendation = next((r for r in recommendations if r['id'] == recommendation_id), None)
    
    if not recommendation:
        return False
    
    if recommendation['type'] == 'task_assignment' and action_data:
        from app.services.task_distributor import assign_task_automatically
        task_id = action_data.get('task_id') or recommendation.get('action_data', {}).get('task_id')
        user_id = action_data.get('user_id') or recommendation.get('action_data', {}).get('user_id')
        
        if task_id and user_id:
            # Здесь можно добавить логику ручного назначения
            # Пока используем автоматическое назначение
            assignment = assign_task_automatically(task_id, user_id)
            return assignment is not None
    
    # Для других типов рекомендаций можно добавить соответствующую логику
    return True

