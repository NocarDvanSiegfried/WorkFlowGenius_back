from flask import Blueprint, request, jsonify

from app.database import db
from app.models import Task, TaskComment, User, Notification

task_comments_bp = Blueprint('task_comments', __name__)

@task_comments_bp.route('/tasks/<int:task_id>/comments', methods=['GET'])
def get_task_comments(task_id):
    """Получить комментарии к задаче"""
    task = Task.query.get_or_404(task_id)
    
    comments = TaskComment.query.filter_by(task_id=task_id).order_by(TaskComment.created_at.desc()).all()
    
    return jsonify({
        'success': True,
        'data': [comment.to_dict() for comment in comments]
    }), 200

@task_comments_bp.route('/tasks/<int:task_id>/comments', methods=['POST'])
def create_task_comment(task_id):
    """Создать комментарий к задаче"""
    task = Task.query.get_or_404(task_id)
    # Без авторизации - берем первого менеджера
    user = User.query.filter_by(role='manager').first()
    user_id = user.id if user else 1
    
    if not request.json or not request.json.get('content'):
        return jsonify({
            'success': False,
            'message': 'Отсутствует содержимое комментария'
        }), 400
    
    content = request.json.get('content', '').strip()
    if not content:
        return jsonify({
            'success': False,
            'message': 'Комментарий не может быть пустым'
        }), 400
    
    comment = TaskComment(
        task_id=task_id,
        user_id=user_id,
        content=content
    )
    
    db.session.add(comment)
    
    # Создаем уведомление для создателя задачи и назначенных сотрудников
    notification_users = {task.created_by}
    for assignment in task.assignments:
        if assignment.assigned_to:
            notification_users.add(assignment.assigned_to)
    
    notification_users.discard(user_id)  # Не уведомляем автора комментария
    
    for notif_user_id in notification_users:
        notification = Notification(
            user_id=notif_user_id,
            type='comment_added',
            title='Новый комментарий к задаче',
            message=f'Добавлен комментарий к задаче "{task.title}"',
            related_task_id=task_id,
            is_read=False
        )
        db.session.add(notification)
    
    db.session.commit()
    
    return jsonify({
        'success': True,
        'data': comment.to_dict(),
        'message': 'Комментарий успешно добавлен'
    }), 201

@task_comments_bp.route('/comments/<int:comment_id>', methods=['PUT'])
def update_task_comment(comment_id):
    """Обновить комментарий"""
    comment = TaskComment.query.get_or_404(comment_id)
    # Без авторизации - разрешаем обновление
    
    if not request.json or not request.json.get('content'):
        return jsonify({
            'success': False,
            'message': 'Отсутствует содержимое комментария'
        }), 400
    
    content = request.json.get('content', '').strip()
    if not content:
        return jsonify({
            'success': False,
            'message': 'Комментарий не может быть пустым'
        }), 400
    
    comment.content = content
    db.session.commit()
    
    return jsonify({
        'success': True,
        'data': comment.to_dict(),
        'message': 'Комментарий успешно обновлен'
    }), 200

@task_comments_bp.route('/comments/<int:comment_id>', methods=['DELETE'])
def delete_task_comment(comment_id):
    """Удалить комментарий"""
    comment = TaskComment.query.get_or_404(comment_id)
    # Без авторизации - разрешаем удаление
    
    db.session.delete(comment)
    db.session.commit()
    
    return jsonify({
        'success': True,
        'message': 'Комментарий успешно удален'
    }), 200

