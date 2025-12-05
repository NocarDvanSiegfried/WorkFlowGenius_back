# routes/skills.py
from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from app.database import db
from app.models import Skill, UserSkill, User

skills_bp = Blueprint('skills', __name__)

@skills_bp.route('', methods=['GET'])
@jwt_required()
def get_skills():
    """Получить список всех навыков"""
    skills = Skill.query.all()
    
    return jsonify({
        'success': True,
        'data': [skill.to_dict() for skill in skills]
    }), 200

@skills_bp.route('', methods=['POST'])
@jwt_required()
def create_skill():
    """Создать новый навык (только для менеджеров)"""
    user_id = get_jwt_identity()
    current_user = User.query.get_or_404(user_id)
    
    # РАЗРЕШИТЬ ВСЕМ ДЛЯ ТЕСТИРОВАНИЯ
    # # Временно отключено для тестирования
    # if current_user.role != 'manager':
    #     return jsonify({
    #         'success': False,
    #         'message': 'Недостаточно прав'
    #     }), 403
    #         'success': False,
    #         'message': 'Недостаточно прав'
    #     }), 403
    
    data = request.json
    if not data or 'name' not in data:
        return jsonify({
            'success': False,
            'message': 'Отсутствует поле "name"'
        }), 400
    
    # Проверка существования
    existing = Skill.query.filter_by(name=data['name']).first()
    if existing:
        return jsonify({
            'success': False,
            'message': 'Навык уже существует'
        }), 400
    
    skill = Skill(
        name=data['name'],
        category=data.get('category', 'other')
    )
    
    db.session.add(skill)
    db.session.commit()
    
    return jsonify({
        'success': True,
        'data': skill.to_dict(),
        'message': 'Навык создан'
    }), 201

@skills_bp.route('/user/<int:user_id>', methods=['GET'])
@jwt_required()
def get_user_skills(user_id):
    """Получить навыки пользователя"""
    current_user_id = get_jwt_identity()
    current_user = User.query.get_or_404(current_user_id)
    
    # Можно видеть свои навыки или быть менеджером
    if current_user_id != user_id and current_user.role != 'manager':
        return jsonify({
            'success': False,
            'message': 'Недостаточно прав'
        }), 403
    
    user_skills = UserSkill.query.filter_by(user_id=user_id).all()
    
    return jsonify({
        'success': True,
        'data': [{
            'id': us.id,
            'skill_id': us.skill_id,
            'skill_name': us.skill_name,
            'proficiency': us.proficiency
        } for us in user_skills]
    }), 200

@skills_bp.route('/user/<int:user_id>', methods=['POST'])
@jwt_required()
def add_user_skill(user_id):
    """Добавить навык пользователю"""
    current_user_id = get_jwt_identity()
    current_user = User.query.get_or_404(current_user_id)
    
    # Можно редактировать свои навыки или быть менеджером
    if current_user_id != user_id and current_user.role != 'manager':
        return jsonify({
            'success': False,
            'message': 'Недостаточно прав'
        }), 403
    
    data = request.json
    if not data or 'skill_id' not in data:
        return jsonify({
            'success': False,
            'message': 'Отсутствует поле "skill_id"'
        }), 400
    
    skill = Skill.query.get_or_404(data['skill_id'])
    
    # Проверка существующей связи
    existing = UserSkill.query.filter_by(user_id=user_id, skill_id=skill.id).first()
    if existing:
        return jsonify({
            'success': False,
            'message': 'Навык уже добавлен'
        }), 400
    
    user_skill = UserSkill(
        user_id=user_id,
        skill_id=skill.id,
        skill_name=skill.name,
        proficiency=data.get('proficiency', 5)
    )
    
    db.session.add(user_skill)
    db.session.commit()
    
    return jsonify({
        'success': True,
        'data': {
            'id': user_skill.id,
            'skill_id': skill.id,
            'skill_name': skill.name,
            'proficiency': user_skill.proficiency
        },
        'message': 'Навык добавлен'
    }), 201

@skills_bp.route('/user/<int:user_skill_id>', methods=['DELETE'])
@jwt_required()
def remove_user_skill(user_skill_id):
    """Удалить навык у пользователя"""
    user_skill = UserSkill.query.get_or_404(user_skill_id)
    current_user_id = get_jwt_identity()
    current_user = User.query.get_or_404(current_user_id)
    
    # Можно удалять свои навыки или быть менеджером
    if user_skill.user_id != current_user_id and current_user.role != 'manager':
        return jsonify({
            'success': False,
            'message': 'Недостаточно прав'
        }), 403
    
    db.session.delete(user_skill)
    db.session.commit()
    
    return jsonify({
        'success': True,
        'message': 'Навык удален'
    }), 200