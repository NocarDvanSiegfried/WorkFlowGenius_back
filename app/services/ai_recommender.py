from app.database import db
from app.models import User, Task, UserSkill, AIRecommendation
from datetime import datetime
from app.services.ml_service import ml_service

def generate_task_recommendations(tasks, employees, max_recommendations=5):
    """Генерировать рекомендации по назначению задач"""
    recommendations = []
    
    for task in tasks:
        # Найти подходящих сотрудников
        suitable_employees = find_suitable_employees_for_task(task, employees)
        
        for employee in suitable_employees[:max_recommendations]:
            # Расчет confidence score с использованием ML
            employee_data = {
                'satisfaction': employee.satisfaction_score,
                'evaluation': employee.efficiency_score,
                'projects_count': employee.current_workload // 10 + 1,
                'monthly_hours': employee.monthly_hours,
                'salary': employee.salary,
                'skills': employee.skills[0].skill_name if employee.skills else 'Python',
                'efficiency': employee.efficiency_score
            }
            
            task_data = {
                'description': task.title,
                'complexity': estimate_task_complexity(task),
                'priority': task.priority
            }
            
            confidence = ml_service.predict_suitability(employee_data, task_data)
            
            if confidence > 0.6:
                recommendation = {
                    'user_id': employee.id,
                    'task_id': task.id,
                    'title': f'Оптимальное назначение: {task.title}',
                    'description': f'AI рекомендует {employee.name} для задачи "{task.title}". '
                                  f'Совместимость на основе навыков и загруженности: {confidence:.0%}.',
                    'priority': 'high' if task.priority in ['urgent', 'high'] else 'medium',
                    'confidence': confidence,
                    'suitability_score': confidence
                }
                recommendations.append(recommendation)
    
    return recommendations

def find_suitable_employees_for_task(task, employees):
    """Найти подходящих сотрудников для задачи"""
    suitable = []
    
    # Анализ описания задачи для определения требуемых навыков
    required_skills = extract_skills_from_task(task)
    
    for employee in employees:
        if employee.role != 'employee':
            continue
            
        # Проверка загруженности
        workload_ratio = employee.current_workload / employee.max_workload if employee.max_workload > 0 else 0
        if workload_ratio > 0.9:
            continue  # Слишком загружен
        
        # Проверка навыков
        employee_skills = [us.skill_name for us in employee.skills]
        skill_match_score = calculate_skill_match(required_skills, employee_skills)
        
        if skill_match_score > 0.3 or not required_skills:
            suitable.append({
                'employee': employee,
                'skill_match': skill_match_score,
                'workload_score': 1 - workload_ratio,
                'efficiency_score': employee.efficiency_score / 10
            })
    
    # Сортировка по общей пригодности
    suitable.sort(key=lambda x: 
        x['skill_match'] * 0.5 + 
        x['workload_score'] * 0.3 + 
        x['efficiency_score'] * 0.2, 
        reverse=True)
    
    return [item['employee'] for item in suitable]

def extract_skills_from_task(task):
    """Извлечь требуемые навыки из описания задачи"""
    required_skills = []
    
    if not task.description:
        return required_skills
    
    description_lower = task.description.lower()
    
    skill_keywords = {
        'Python': ['python', 'django', 'flask', 'pandas', 'numpy', 'fastapi'],
        'JavaScript': ['javascript', 'react', 'vue', 'angular', 'node', 'typescript', 'js'],
        'Design': ['design', 'ui', 'ux', 'figma', 'sketch', 'prototype', 'interface'],
        'Database': ['database', 'sql', 'postgresql', 'mysql', 'mongodb', 'redis', 'postgres'],
        'DevOps': ['docker', 'kubernetes', 'aws', 'azure', 'ci/cd', 'devops', 'deploy'],
        'Machine Learning': ['machine learning', 'ml', 'ai', 'neural', 'tensorflow', 'pytorch'],
        'API': ['api', 'rest', 'graphql', 'endpoint', 'microservice', 'json'],
        'Testing': ['test', 'testing', 'unit test', 'integration', 'qa', 'quality'],
        'Security': ['security', 'secure', 'authentication', 'authorization', 'jwt', 'oauth'],
    }
    
    for skill, keywords in skill_keywords.items():
        for keyword in keywords:
            if keyword in description_lower:
                if skill not in required_skills:
                    required_skills.append(skill)
                break
    
    return required_skills

def calculate_skill_match(required_skills, employee_skills):
    """Рассчитать совпадение навыков"""
    if not required_skills:
        return 0.5  # Базовый балл если навыки не требуются
    
    matches = sum(1 for skill in required_skills if skill in employee_skills)
    return matches / len(required_skills)

def estimate_task_complexity(task):
    """Оценить сложность задачи"""
    if task.estimated_hours:
        if task.estimated_hours > 20:
            return 'Extreme'
        elif task.estimated_hours > 10:
            return 'Critical'
        elif task.estimated_hours > 5:
            return 'High'
        else:
            return 'Medium'
    elif task.priority == 'urgent':
        return 'High'
    else:
        return 'Medium'