"""
Схемы валидации для API команды
"""
from marshmallow import Schema, fields, validate


class UserCompetencySchema(Schema):
    """Схема компетенции пользователя"""
    id = fields.Int(dump_only=True)
    user_id = fields.Int(dump_only=True)
    skill_name = fields.Str(required=True, validate=validate.Length(min=1, max=100))
    experience_years = fields.Float(missing=0.0)
    level = fields.Str(missing='intermediate', validate=validate.OneOf(['beginner', 'intermediate', 'advanced', 'expert']))


class WorkPreferenceSchema(Schema):
    """Схема предпочтений времени работы"""
    id = fields.Int(dump_only=True)
    user_id = fields.Int(dump_only=True)
    preferred_start_time = fields.Str(allow_none=True)
    preferred_end_time = fields.Str(allow_none=True)
    preferred_days = fields.List(fields.Str(), allow_none=True)
    timezone = fields.Str(missing='UTC')


class TeamMemberSchema(Schema):
    """Схема члена команды"""
    id = fields.Int()
    email = fields.Str()
    name = fields.Str()
    role = fields.Str()
    current_workload = fields.Int()
    max_workload = fields.Int()
    satisfaction = fields.Int()
    efficiency = fields.Int()
    avg_hours_per_month = fields.Int()
    salary = fields.Str(allow_none=True)
    skills = fields.Str(allow_none=True)
    competencies = fields.Nested(UserCompetencySchema, many=True, allow_none=True)
    work_preference = fields.Nested(WorkPreferenceSchema, allow_none=True)
    metrics = fields.Dict(allow_none=True)

