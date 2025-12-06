from marshmallow import Schema, fields, validate

class TaskSchema(Schema):
    id = fields.Int(dump_only=True)
    title = fields.Str(required=True, validate=validate.Length(min=1, max=255))
    description = fields.Str(allow_none=True)
    priority = fields.Str(validate=validate.OneOf(['low', 'medium', 'high', 'urgent']), missing='medium')
    status = fields.Str(validate=validate.OneOf(['pending', 'assigned', 'in_progress', 'completed', 'cancelled']), missing='pending')
    deadline = fields.DateTime(allow_none=True, format='iso')
    estimated_hours = fields.Float(allow_none=True, validate=validate.Range(min=0))
    rating = fields.Int(allow_none=True, validate=validate.Range(min=1, max=5))
    created_by = fields.Int(dump_only=True)
    created_at = fields.DateTime(dump_only=True, format='iso')
    updated_at = fields.DateTime(dump_only=True, format='iso')

class CreateTaskSchema(Schema):
    title = fields.Str(required=True, validate=validate.Length(min=1, max=255))
    description = fields.Str(allow_none=True)
    priority = fields.Str(validate=validate.OneOf(['low', 'medium', 'high', 'urgent']), missing='medium')
    deadline = fields.DateTime(allow_none=True, format='iso')
    estimated_hours = fields.Float(allow_none=True, validate=validate.Range(min=0))
    rating = fields.Int(allow_none=True, validate=validate.Range(min=1, max=5))

