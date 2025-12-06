"""
Сервис анализа компетенций сотрудников
"""
from app.database import db
from app.models import User, UserCompetency, Task


def get_user_competencies(user_id):
    """Получить компетенции пользователя"""
    competencies = UserCompetency.query.filter_by(user_id=user_id).all()
    return [c.to_dict() for c in competencies]


def calculate_competence_match(user_id, task_description):
    """
    Рассчитать соответствие компетенций пользователя задаче
    
    Args:
        user_id: ID пользователя
        task_description: Описание задачи
        
    Returns:
        float: Оценка соответствия (0-1)
    """
    competencies = UserCompetency.query.filter_by(user_id=user_id).all()
    if not competencies:
        return 0.5  # Средняя оценка если нет компетенций
    
    task_lower = task_description.lower() if task_description else ''
    
    # Простой алгоритм: проверяем совпадение навыков в описании задачи
    matches = 0
    total_weight = 0
    
    for comp in competencies:
        skill_lower = comp.skill_name.lower()
        weight = 1.0
        
        # Вес в зависимости от уровня
        if comp.level == 'expert':
            weight = 1.0
        elif comp.level == 'advanced':
            weight = 0.8
        elif comp.level == 'intermediate':
            weight = 0.6
        else:
            weight = 0.4
        
        # Учитываем опыт
        experience_multiplier = min(comp.experience_years / 5.0, 1.0)
        weight *= (0.5 + 0.5 * experience_multiplier)
        
        if skill_lower in task_lower:
            matches += weight
        
        total_weight += weight
    
    if total_weight == 0:
        return 0.5
    
    return min(matches / total_weight, 1.0)


def get_competence_score(user_id, required_skills):
    """
    Получить оценку компетенций пользователя для требуемых навыков
    
    Args:
        user_id: ID пользователя
        required_skills: Список требуемых навыков
    
    Returns:
        float: Оценка (0-1)
    """
    competencies = UserCompetency.query.filter_by(user_id=user_id).all()
    user_skills = {c.skill_name.lower(): c for c in competencies}
    
    if not required_skills:
        return 0.5
    
    matches = 0
    total = len(required_skills)
    
    for skill in required_skills:
        skill_lower = skill.lower()
        if skill_lower in user_skills:
            comp = user_skills[skill_lower]
            score = 0.5
            
            # Оценка в зависимости от уровня
            if comp.level == 'expert':
                score = 1.0
            elif comp.level == 'advanced':
                score = 0.8
            elif comp.level == 'intermediate':
                score = 0.6
            else:
                score = 0.4
            
            # Учитываем опыт
            experience_bonus = min(comp.experience_years / 5.0, 0.3)
            score += experience_bonus
            
            matches += min(score, 1.0)
    
    return matches / total if total > 0 else 0.5

