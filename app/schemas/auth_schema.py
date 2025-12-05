from marshmallow import Schema, fields, validate

class RegisterSchema(Schema):
    email = fields.Email(required=True)
    name = fields.Str(required=True, validate=validate.Length(min=2, max=255))
    position = fields.Str(validate=validate.Length(max=255))
    password = fields.Str(required=True, validate=validate.Length(min=6))
    role = fields.Str(validate=validate.OneOf(['manager', 'employee', 'admin']), missing='employee')
    satisfaction_score = fields.Int(validate=validate.Range(min=1, max=10), missing=7)
    efficiency_score = fields.Int(validate=validate.Range(min=1, max=10), missing=8)
    monthly_hours = fields.Int(validate=validate.Range(min=1), missing=160)
    salary = fields.Int(validate=validate.Range(min=0), allow_none=True)
    skills = fields.List(fields.Str(), missing=[])

class LoginSchema(Schema):
    email = fields.Email(required=True)
    password = fields.Str(required=True)