from flask import Blueprint
from app.routes.auth import auth_bp
from app.routes.tasks import tasks_bp
from app.routes.users import users_bp
from app.routes.dashboard import dashboard_bp
from app.routes.health import health_bp
from app.routes.team import team_bp
from app.routes.team_dna import team_dna_bp
from app.routes.ai_settings import ai_settings_bp
from app.routes.analytics import analytics_bp
from app.routes.ai_recommendations import ai_recommendations_bp
from app.routes.task_comments import task_comments_bp
from app.routes.notifications import notifications_bp
from app.routes.task_history import task_history_bp
from app.routes.task_tags import task_tags_bp
from app.routes.time_tracking import time_tracking_bp

def register_blueprints(app):
    """Регистрация всех Blueprints"""
    app.register_blueprint(health_bp, url_prefix='/api')
    app.register_blueprint(auth_bp, url_prefix='/api/auth')
    app.register_blueprint(tasks_bp, url_prefix='/api/tasks')
    app.register_blueprint(users_bp, url_prefix='/api/users')
    app.register_blueprint(dashboard_bp, url_prefix='/api/dashboard')
    app.register_blueprint(team_bp, url_prefix='/api/team')
    app.register_blueprint(team_dna_bp, url_prefix='/api/team-dna')
    app.register_blueprint(ai_settings_bp, url_prefix='/api/ai-settings')
    app.register_blueprint(analytics_bp, url_prefix='/api/analytics')
    app.register_blueprint(ai_recommendations_bp, url_prefix='/api/ai-recommendations')
    app.register_blueprint(task_comments_bp, url_prefix='/api')
    app.register_blueprint(notifications_bp, url_prefix='/api/notifications')
    app.register_blueprint(task_history_bp, url_prefix='/api')
    app.register_blueprint(task_tags_bp, url_prefix='/api')
    app.register_blueprint(time_tracking_bp, url_prefix='/api')

