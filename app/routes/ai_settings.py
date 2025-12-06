"""
API endpoints для настроек ИИ
"""
from flask import Blueprint, request, jsonify

from app.models import User
from app.services.ai_settings_service import get_settings, update_settings

ai_settings_bp = Blueprint('ai_settings', __name__)


@ai_settings_bp.route('', methods=['GET'])
def get_ai_settings():
    """Получить настройки ИИ"""
    # Без авторизации - просто возвращаем настройки
    settings = get_settings()
    
    return jsonify({
        'success': True,
        'data': settings.to_dict()
    }), 200


@ai_settings_bp.route('', methods=['PUT'])
def update_ai_settings():
    """Обновить настройки ИИ"""
    # Без авторизации - просто обновляем настройки
    
    if not request.json:
        return jsonify({
            'success': False,
            'message': 'Отсутствуют данные'
        }), 400
    
    data = request.json
    
    # Валидация весов (должны быть 0-100)
    weight_fields = ['competence_weight', 'load_weight', 'time_preference_weight', 'priority_weight']
    for field in weight_fields:
        if field in data:
            value = int(data[field])
            if value < 0 or value > 100:
                return jsonify({
                    'success': False,
                    'message': f'{field} должен быть в диапазоне 0-100'
                }), 400
    
    settings = update_settings(**data)
    
    return jsonify({
        'success': True,
        'data': settings.to_dict(),
        'message': 'Настройки успешно обновлены'
    }), 200

