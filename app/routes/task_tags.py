from flask import Blueprint, request, jsonify

from app.database import db
from app.models import Task, TaskTag

task_tags_bp = Blueprint('task_tags', __name__)

@task_tags_bp.route('/tasks/<int:task_id>/tags', methods=['GET'])
def get_task_tags(task_id):
    """Получить теги задачи"""
    task = Task.query.get_or_404(task_id)
    
    return jsonify({
        'success': True,
        'data': [tag.to_dict() for tag in task.tags]
    }), 200

@task_tags_bp.route('/tasks/<int:task_id>/tags', methods=['POST'])
def add_task_tag(task_id):
    """Добавить тег к задаче"""
    task = Task.query.get_or_404(task_id)
    
    if not request.json or not request.json.get('tag_name'):
        return jsonify({
            'success': False,
            'message': 'Отсутствует название тега'
        }), 400
    
    tag_name = request.json.get('tag_name', '').strip()
    color = request.json.get('color', 'blue')
    
    if not tag_name:
        return jsonify({
            'success': False,
            'message': 'Название тега не может быть пустым'
        }), 400
    
    # Проверка: тег уже существует?
    existing_tag = TaskTag.query.filter_by(task_id=task_id, tag_name=tag_name).first()
    if existing_tag:
        return jsonify({
            'success': False,
            'message': 'Тег уже существует'
        }), 400
    
    tag = TaskTag(
        task_id=task_id,
        tag_name=tag_name,
        color=color
    )
    
    db.session.add(tag)
    db.session.commit()
    
    return jsonify({
        'success': True,
        'data': tag.to_dict(),
        'message': 'Тег успешно добавлен'
    }), 201

@task_tags_bp.route('/tasks/<int:task_id>/tags/<int:tag_id>', methods=['DELETE'])
def delete_task_tag(task_id, tag_id):
    """Удалить тег из задачи"""
    tag = TaskTag.query.filter_by(id=tag_id, task_id=task_id).first_or_404()
    
    db.session.delete(tag)
    db.session.commit()
    
    return jsonify({
        'success': True,
        'message': 'Тег успешно удален'
    }), 200

