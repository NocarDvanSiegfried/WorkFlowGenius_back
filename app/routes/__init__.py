# app/routes/__init__.py
from app.routes.auth import auth_bp
from app.routes.tasks import tasks_bp
from app.routes.users import users_bp
from app.routes.assignments import assignments_bp
from app.routes.analytics import analytics_bp
from app.routes.dashboard import dashboard_bp
from app.routes.skills import skills_bp
from app.routes.health import health_bp
from app.routes.main import main_bp
from app.routes.ai import ai_bp
from app.routes.admin import admin_bp  # Будет создан позже

def register_blueprints(app):
    # Основные API endpoints
    app.register_blueprint(main_bp, url_prefix='/')
    
    app.register_blueprint(auth_bp, url_prefix='/api/auth')
    app.register_blueprint(tasks_bp, url_prefix='/api/tasks')
    app.register_blueprint(users_bp, url_prefix='/api/users')
    app.register_blueprint(assignments_bp, url_prefix='/api/assignments')
    app.register_blueprint(analytics_bp, url_prefix='/api/analytics')
    app.register_blueprint(dashboard_bp, url_prefix='/api/dashboard')
    app.register_blueprint(skills_bp, url_prefix='/api/skills')
    app.register_blueprint(ai_bp, url_prefix='/api/ai')
    app.register_blueprint(admin_bp, url_prefix='/api/admin')
    app.register_blueprint(health_bp, url_prefix='/api')