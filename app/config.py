# config.py - ОБНОВЛЕННАЯ ВЕРСИЯ
import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    """Базовая конфигурация приложения - ОБНОВЛЕННАЯ"""
    SECRET_KEY = os.getenv('SECRET_KEY', 'dev-secret-key-change-in-production')
    JWT_SECRET_KEY = os.getenv('JWT_SECRET_KEY', 'jwt-secret-key-change-in-production')
    JWT_ACCESS_TOKEN_EXPIRES = int(os.getenv('JWT_ACCESS_TOKEN_EXPIRES', 3600))  # 1 час
    
    # База данных
    basedir = os.path.abspath(os.path.dirname(os.path.dirname(__file__)))
    SQLALCHEMY_DATABASE_URI = os.getenv(
        'DATABASE_URL',
        f"sqlite:///{os.path.join(basedir, 'instance', 'app.db')}"
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # CORS
    CORS_ORIGINS = os.getenv('CORS_ORIGINS', 'http://localhost:5173').split(',')
    
    # AI и производительность
    AI_ENABLED = os.getenv('AI_ENABLED', 'true').lower() == 'true'
    PERFORMANCE_UPDATE_INTERVAL = int(os.getenv('PERFORMANCE_UPDATE_INTERVAL', 86400))  # 24 часа
    MAX_WORKLOAD_THRESHOLD = float(os.getenv('MAX_WORKLOAD_THRESHOLD', 0.9))  # 90%
    
    # Окружение
    DEBUG = os.getenv('FLASK_ENV', 'development') == 'development'
    FLASK_ENV = os.getenv('FLASK_ENV', 'development')
    
    # Логирование
    LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO')