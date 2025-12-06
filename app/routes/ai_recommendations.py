"""
API endpoints для рекомендаций ИИ
"""
from flask import Blueprint, request, jsonify

from app.models import User
from app.services.ai_recommendations_service import generate_recommendations, apply_recommendation

ai_recommendations_bp = Blueprint('ai_recommendations', __name__)


@ai_recommendations_bp.route('', methods=['GET'])
def get_recommendations():
    """Получить список рекомендаций ИИ"""
    # Без авторизации - просто возвращаем рекомендации
    recommendations = generate_recommendations()
    
    return jsonify({
        'success': True,
        'data': recommendations
    }), 200


@ai_recommendations_bp.route('/<recommendation_id>/apply', methods=['POST'])
def apply_recommendation_endpoint(recommendation_id):
    """Применить рекомендацию"""
    # Без авторизации - просто применяем рекомендацию
    
    action_data = request.json if request.json else {}
    
    success = apply_recommendation(recommendation_id, action_data)
    
    if success:
        return jsonify({
            'success': True,
            'message': 'Рекомендация успешно применена'
        }), 200
    
    return jsonify({
        'success': False,
        'message': 'Не удалось применить рекомендацию'
    }), 400

