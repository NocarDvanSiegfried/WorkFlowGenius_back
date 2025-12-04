from marshmallow import Schema, fields, validate

class RegisterSchema(Schema):
    email = fields.Email(required=True)
    name = fields.Str(required=True, validate=validate.Length(min=2, max=255))
    password = fields.Str(required=True, validate=validate.Length(min=6))
    role = fields.Str(validate=validate.OneOf(['manager', 'employee']), missing='employee')

class LoginSchema(Schema):
    email = fields.Email(required=True)
    password = fields.Str(required=True)

