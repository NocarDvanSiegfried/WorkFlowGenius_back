from flask import Blueprint, request, jsonify
from werkzeug.security import generate_password_hash, check_password_hash
from flask_jwt_extended import create_access_token, jwt_required, get_jwt_identity
from app.database import db
from app.models import User
from app.schemas.auth_schema import RegisterSchema, LoginSchema

auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/register', methods=['POST'])
def register():
    """Регистрация нового пользователя"""
    if not request.json:
        return jsonify({
            'success': False,
            'message': 'Отсутствуют данные'
        }), 400
    
    schema = RegisterSchema()
    try:
        data = schema.load(request.json)
    except Exception as e:
        return jsonify({
            'success': False,
            'message': 'Ошибка валидации',
            'errors': str(e)
        }), 400
    
    # Проверка существования пользователя
    if User.query.filter_by(email=data['email']).first():
        return jsonify({
            'success': False,
            'message': 'Пользователь с таким email уже существует'
        }), 400
    
    # Создание пользователя
    user = User(
        email=data['email'],
        name=data['name'],
        password_hash=generate_password_hash(data['password']),
        role=data.get('role', 'employee')
    )
    
    db.session.add(user)
    db.session.commit()
    
    # Создание токена
    access_token = create_access_token(identity=str(user.id))
    
    return jsonify({
        'success': True,
        'data': {
            'user': user.to_dict(),
            'access_token': access_token
        },
        'message': 'Пользователь успешно зарегистрирован'
    }), 201

@auth_bp.route('/login', methods=['POST'])
def login():
    """Вход пользователя"""
    if not request.json:
        return jsonify({
            'success': False,
            'message': 'Отсутствуют данные'
        }), 400
    
    schema = LoginSchema()
    try:
        data = schema.load(request.json)
    except Exception as e:
        return jsonify({
            'success': False,
            'message': 'Ошибка валидации',
            'errors': str(e)
        }), 400
    
    # Поиск пользователя
    user = User.query.filter_by(email=data['email']).first()
    
    if not user or not check_password_hash(user.password_hash, data['password']):
        return jsonify({
            'success': False,
            'message': 'Неверный email или пароль'
        }), 401
    
    # Создание токена
    access_token = create_access_token(identity=str(user.id))
    
    return jsonify({
        'success': True,
        'data': {
            'user': user.to_dict(),
            'access_token': access_token
        },
        'message': 'Успешный вход'
    }), 200

@auth_bp.route('/me', methods=['GET'])
@jwt_required()
def get_current_user():
    """Получить текущего пользователя"""
    user_id = get_jwt_identity()
    user = User.query.get_or_404(user_id)
    
    return jsonify({
        'success': True,
        'data': user.to_dict()
    }), 200

