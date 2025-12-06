"""
Сервис управления настройками ИИ
"""
from app.database import db
from app.models import AISettings


def get_settings():
    """Получить настройки ИИ (или создать дефолтные)"""
    settings = AISettings.query.first()
    if not settings:
        settings = AISettings()
        db.session.add(settings)
        db.session.commit()
    return settings


def update_settings(**kwargs):
    """
    Обновить настройки ИИ
    
    Args:
        **kwargs: Параметры для обновления
    
    Returns:
        AISettings: Обновленный объект настроек
    """
    settings = get_settings()
    
    allowed_fields = [
        'competence_weight', 'load_weight', 'time_preference_weight', 'priority_weight',
        'auto_balance_enabled', 'predict_completion_enabled', 'smart_recommendations_enabled',
        'continuous_learning_enabled', 'anonymization_enabled', 'model_update_frequency'
    ]
    
    for field, value in kwargs.items():
        if field in allowed_fields and hasattr(settings, field):
            setattr(settings, field, value)
    
    from datetime import datetime
    settings.updated_at = datetime.utcnow()
    db.session.commit()
    
    return settings

