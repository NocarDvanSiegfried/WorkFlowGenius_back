# services/task_distributor.py - УЛУЧШЕННАЯ ВЕРСИЯ
from app.database import db
from app.models import User, Task, Assignment, UserSkill
from datetime import datetime

def assign_task_automatically(task_id, assigned_by):
    """
    Автоматически назначить задачу сотруднику
    
    Улучшенный алгоритм:
    1. Анализ требований задачи (если есть описание)
    2. Поиск сотрудников с подходящими навыками
    3. Учет текущей загруженности
    4. Учет эффективности сотрудника
    5. Выбор оптимального кандидата
    """
    task = Task.query.get(task_id)
    if not task:
        return None
    
    # Проверка: задача уже назначена?
    existing_assignment = Assignment.query.filter_by(task_id=task_id, status='assigned').first()
    if existing_assignment:
        return existing_assignment
    
    # Поиск ключевых слов в описании задачи для определения требуемых навыков
    required_skills = []
    if task.description:
        # Простой анализ текста (можно заменить на NLP)
        description_lower = task.description.lower()
        skill_keywords = {
            'python': ['python', 'django', 'flask'],
            'javascript': ['javascript', 'react', 'vue', 'node'],
            'design': ['design', 'ui', 'ux', 'figma'],
            'database': ['database', 'sql', 'postgresql', 'mysql'],
            'api': ['api', 'rest', 'graphql'],
            'machine learning': ['machine learning', 'ml', 'ai', 'neural']
        }
        
        for skill, keywords in skill_keywords.items():
            for keyword in keywords:
                if keyword in description_lower:
                    required_skills.append(skill)
                    break
    
    # Получить всех доступных сотрудников
    available_users = User.query.filter(
        User.role == 'employee',
        User.current_workload < User.max_workload
    ).all()
    
    if not available_users:
        return None
    
    # Оценка кандидатов
    candidates = []
    for user in available_users:
        score = 0
        
        # 1. Загруженность (чем меньше, тем лучше)
        workload_ratio = user.current_workload / user.max_workload if user.max_workload > 0 else 0
        workload_score = (1 - workload_ratio) * 40  # 40% от общей оценки
        
        # 2. Совпадение навыков
        skill_score = 0
        if required_skills:
            user_skills = [us.skill_name.lower() for us in user.skills]
            matches = 0
            for req_skill in required_skills:
                if any(req_skill in us for us in user_skills):
                    matches += 1
            skill_match_ratio = matches / len(required_skills) if required_skills else 0
            skill_score = skill_match_ratio * 40  # 40% от общей оценки
        else:
            # Если навыки не требуются, даём базовый балл
            skill_score = 20
        
        # 3. Эффективность сотрудника
        efficiency_score = user.efficiency_score * 2  # 20% от общей оценки (1-10 → 0-20)
        
        total_score = workload_score + skill_score + efficiency_score
        
        candidates.append({
            'user': user,
            'score': total_score,
            'breakdown': {
                'workload_score': workload_score,
                'skill_score': skill_score,
                'efficiency_score': efficiency_score
            }
        })
    
    # Выбор лучшего кандидата
    candidates.sort(key=lambda x: x['score'], reverse=True)
    selected_candidate = candidates[0]['user']
    
    # Рассчитать workload_points в зависимости от приоритета и сложности
    workload_points = 10
    if task.priority == 'urgent':
        workload_points = 25
    elif task.priority == 'high':
        workload_points = 18
    elif task.priority == 'low':
        workload_points = 7
    
    # Увеличить нагрузку для задач со сложным описанием
    if task.description and len(task.description) > 500:
        workload_points = int(workload_points * 1.3)
    
    # Создать назначение
    assignment = Assignment(
        task_id=task_id,
        assigned_to=selected_candidate.id,
        assigned_by=assigned_by,
        workload_points=workload_points,
        status='assigned'
    )
    
    # Обновить загруженность сотрудника
    selected_candidate.current_workload = min(
        selected_candidate.current_workload + workload_points,
        selected_candidate.max_workload
    )
    
    # Создать рекомендацию ИИ
    from app.models import AIRecommendation
    
    recommendation = AIRecommendation(
        user_id=selected_candidate.id,
        task_id=task_id,
        recommendation_type='task_assignment',
        title='Новая задача назначена',
        description=f'Вам назначена задача "{task.title}" на основе анализа ваших навыков и загруженности.',
        priority='medium',
        confidence_score=0.78
    )
    
    db.session.add(assignment)
    db.session.add(recommendation)
    db.session.commit()
    
    return assignment