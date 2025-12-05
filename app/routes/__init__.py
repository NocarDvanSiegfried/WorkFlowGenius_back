# routes/__init__.py - ОБНОВЛЕННАЯ ВЕРСИЯ
from flask import Blueprint

# Импорт всех Blueprints
from app.routes.auth import auth_bp
from app.routes.tasks import tasks_bp
from app.routes.users import users_bp
from app.routes.dashboard import dashboard_bp
from app.routes.health import health_bp
from app.routes.main import main_bp
from app.routes.admin import admin_bp
from app.routes.assigments import assignments_bp
from app.routes.ai_recommendations import ai_bp
from app.routes.analytics import analytics_bp
from app.routes.skills import skills_bp

def register_blueprints(app):
    """Регистрация всех Blueprints"""
    app.register_blueprint(main_bp)
    app.register_blueprint(health_bp, url_prefix='/api')
    app.register_blueprint(auth_bp, url_prefix='/api/auth')
    app.register_blueprint(tasks_bp, url_prefix='/api/tasks')
    app.register_blueprint(users_bp, url_prefix='/api/users')
    app.register_blueprint(dashboard_bp, url_prefix='/api/dashboard')
    app.register_blueprint(admin_bp, url_prefix='/api/admin')
    app.register_blueprint(assignments_bp, url_prefix='/api/assignments')
    app.register_blueprint(ai_bp, url_prefix='/api/ai')
    app.register_blueprint(analytics_bp, url_prefix='/api/analytics')
    app.register_blueprint(skills_bp, url_prefix='/api/skills')