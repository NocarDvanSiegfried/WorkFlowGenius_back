"""
Схемы валидации для настроек ИИ
"""
from marshmallow import Schema, fields, validate


class AISettingsSchema(Schema):
    """Схема настроек ИИ"""
    id = fields.Int(dump_only=True)
    competence_weight = fields.Int(validate=validate.Range(min=0, max=100), missing=85)
    load_weight = fields.Int(validate=validate.Range(min=0, max=100), missing=90)
    time_preference_weight = fields.Int(validate=validate.Range(min=0, max=100), missing=70)
    priority_weight = fields.Int(validate=validate.Range(min=0, max=100), missing=95)
    auto_balance_enabled = fields.Bool(missing=True)
    predict_completion_enabled = fields.Bool(missing=True)
    smart_recommendations_enabled = fields.Bool(missing=True)
    continuous_learning_enabled = fields.Bool(missing=True)
    anonymization_enabled = fields.Bool(missing=True)
    model_update_frequency = fields.Str(
        validate=validate.OneOf(['daily', 'weekly', 'monthly']),
        missing='daily'
    )
    updated_at = fields.DateTime(dump_only=True)

