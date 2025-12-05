"""
Flask application package
Application Factory Pattern implementation
"""
from flask import Flask
from flask_cors import CORS
from flask_jwt_extended import JWTManager
from app.config import Config
from app.database import db
from app.routes import register_blueprints
from flask_migrate import Migrate
import os

def create_app(config_class=Config):
    """Application Factory Pattern"""
    app = Flask(__name__)
    app.config.from_object(config_class)
    
    # Инициализация расширений
    db.init_app(app)
    migrate = Migrate(app, db) 
    jwt = JWTManager(app)
    CORS(app, origins=app.config['CORS_ORIGINS'])
    
    # Регистрация Blueprints
    register_blueprints(app)
    
    # Регистрация обработчиков ошибок
    from app.middleware.error_handler import register_error_handlers
    register_error_handlers(app)
    
    # Инициализация базы данных
    with app.app_context():
        # Создать директорию instance если её нет
        instance_path = app.instance_path
        if not os.path.exists(instance_path):
            os.makedirs(instance_path)
        # Создание таблиц при первом запуске (только если база пустая)
        try:
            db.create_all()
        except Exception:
            pass  # Таблицы уже существуют
    
    return app

