"""
API endpoints для управления командой
"""
from flask import Blueprint, request, jsonify

from app.database import db
from app.models import User, UserCompetency, WorkPreference
from app.services.analytics_service import get_employee_metrics

team_bp = Blueprint('team', __name__)


@team_bp.route('', methods=['GET'])
def get_team():
    """Получить список команды с метриками"""
    # Без авторизации - просто возвращаем данные команды
    
    employees = User.query.filter_by(role='employee').all()
    
    team_data = []
    for employee in employees:
        employee_dict = employee.to_dict()
        
        # Добавляем компетенции
        competencies = UserCompetency.query.filter_by(user_id=employee.id).all()
        employee_dict['skills'] = ', '.join([c.skill_name for c in competencies]) if competencies else ''
        
        # Добавляем метрики
        metrics = get_employee_metrics(employee.id)
        if metrics:
            employee_dict.update({
                'satisfaction': metrics.get('satisfaction', 0),
                'efficiency': metrics.get('efficiency', 0),
                'projects': metrics.get('projects', 0),
                'avg_hours_per_month': metrics.get('avg_hours_per_month', 0),
                'salary': metrics.get('salary', '0'),
            })
        else:
            # Значения по умолчанию, если метрики недоступны
            employee_dict.update({
                'satisfaction': 0,
                'efficiency': 0,
                'projects': 0,
                'avg_hours_per_month': 0,
                'salary': '0',
            })
        
        team_data.append(employee_dict)
    
    return jsonify({
        'success': True,
        'data': team_data
    }), 200


@team_bp.route('/<int:user_id>', methods=['GET'])
def get_team_member(user_id):
    """Получить информацию о члене команды"""
    # Без авторизации - просто возвращаем данные пользователя
    
    user = User.query.get_or_404(user_id)
    employee_dict = user.to_dict()
    
    # Компетенции
    competencies = UserCompetency.query.filter_by(user_id=user_id).all()
    employee_dict['competencies'] = [c.to_dict() for c in competencies]
    
    # Предпочтения времени работы
    preference = WorkPreference.query.filter_by(user_id=user_id).first()
    employee_dict['work_preference'] = preference.to_dict() if preference else None
    
    # Метрики
    metrics = get_employee_metrics(user_id)
    if metrics:
        employee_dict['metrics'] = metrics
    
    return jsonify({
        'success': True,
        'data': employee_dict
    }), 200


@team_bp.route('/<int:user_id>/competencies', methods=['GET'])
def get_user_competencies(user_id):
    """Получить компетенции пользователя"""
    # Без авторизации - просто возвращаем данные
    
    competencies = UserCompetency.query.filter_by(user_id=user_id).all()
    
    return jsonify({
        'success': True,
        'data': [c.to_dict() for c in competencies]
    }), 200


@team_bp.route('/<int:user_id>/competencies', methods=['POST'])
def add_user_competency(user_id):
    """Добавить компетенцию пользователю"""
    # Без авторизации - просто добавляем компетенцию
    
    if not request.json:
        return jsonify({
            'success': False,
            'message': 'Отсутствуют данные'
        }), 400
    
    data = request.json
    skill_name = data.get('skill_name')
    experience_years = data.get('experience_years', 0)
    level = data.get('level', 'intermediate')
    
    if not skill_name:
        return jsonify({
            'success': False,
            'message': 'Не указано название навыка'
        }), 400
    
    competency = UserCompetency(
        user_id=user_id,
        skill_name=skill_name,
        experience_years=float(experience_years),
        level=level
    )
    
    db.session.add(competency)
    db.session.commit()
    
    return jsonify({
        'success': True,
        'data': competency.to_dict(),
        'message': 'Компетенция успешно добавлена'
    }), 201


@team_bp.route('/<int:user_id>/competencies/<int:competency_id>', methods=['DELETE'])
def delete_user_competency(user_id, competency_id):
    """Удалить компетенцию пользователя"""
    # Без авторизации - просто удаляем компетенцию
    
    competency = UserCompetency.query.filter_by(
        id=competency_id,
        user_id=user_id
    ).first_or_404()
    
    db.session.delete(competency)
    db.session.commit()
    
    return jsonify({
        'success': True,
        'message': 'Компетенция успешно удалена'
    }), 200

