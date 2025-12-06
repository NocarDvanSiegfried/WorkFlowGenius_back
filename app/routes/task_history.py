from flask import Blueprint, request, jsonify

from app.database import db
from app.models import Task, TaskHistory, User

task_history_bp = Blueprint('task_history', __name__)

@task_history_bp.route('/tasks/<int:task_id>/history', methods=['GET'])
def get_task_history(task_id):
    """Получить историю изменений задачи"""
    task = Task.query.get_or_404(task_id)
    
    limit = request.args.get('limit', type=int, default=100)
    
    history = TaskHistory.query.filter_by(task_id=task_id).order_by(TaskHistory.created_at.desc()).limit(limit).all()
    
    return jsonify({
        'success': True,
        'data': [entry.to_dict() for entry in history]
    }), 200

