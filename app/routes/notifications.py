from flask import Blueprint, request, jsonify

from app.database import db
from app.models import Notification, User
from app.services.notification_service import create_deadline_notifications, create_overdue_notifications

notifications_bp = Blueprint('notifications', __name__)

@notifications_bp.route('', methods=['GET'])
def get_notifications():
    """Получить уведомления пользователя"""
    user = User.query.filter_by(role="manager").first()
    
    # Фильтры
    is_read = request.args.get('is_read')
    limit = request.args.get('limit', type=int, default=50)
    
    query = Notification.query.filter_by(user_id=user_id)
    
    if is_read is not None:
        query = query.filter_by(is_read=is_read.lower() == 'true')
    
    notifications = query.order_by(Notification.created_at.desc()).limit(limit).all()
    
    unread_count = Notification.query.filter_by(user_id=user_id, is_read=False).count()
    
    return jsonify({
        'success': True,
        'data': [notif.to_dict() for notif in notifications],
        'unread_count': unread_count
    }), 200

@notifications_bp.route('/<int:notification_id>/read', methods=['PUT'])
def mark_notification_read(notification_id):
    """Отметить уведомление как прочитанное"""
    notification = Notification.query.get_or_404(notification_id)
    user = User.query.filter_by(role="manager").first()
    
    # Проверка прав
    if notification.user_id != user_id:
        return jsonify({
            'success': False,
            'message': 'Недостаточно прав'
        }), 403
    
    notification.is_read = True
    db.session.commit()
    
    return jsonify({
        'success': True,
        'data': notification.to_dict(),
        'message': 'Уведомление отмечено как прочитанное'
    }), 200

@notifications_bp.route('/read-all', methods=['PUT'])
def mark_all_notifications_read():
    """Отметить все уведомления как прочитанные"""
    # Без авторизации - берем первого менеджера
    user = User.query.filter_by(role='manager').first()
    user_id = user.id if user else 1
    
    Notification.query.filter_by(user_id=user_id, is_read=False).update({'is_read': True})
    db.session.commit()
    
    return jsonify({
        'success': True,
        'message': 'Все уведомления отмечены как прочитанные'
    }), 200

@notifications_bp.route('/<int:notification_id>', methods=['DELETE'])
def delete_notification(notification_id):
    """Удалить уведомление"""
    notification = Notification.query.get_or_404(notification_id)
    # Без авторизации - разрешаем удаление
    
    db.session.delete(notification)
    db.session.commit()
    
    return jsonify({
        'success': True,
        'message': 'Уведомление успешно удалено'
    }), 200

@notifications_bp.route('/generate', methods=['POST'])
def generate_notifications():
    """Создать уведомления о дедлайнах (для менеджеров)"""
    # Без авторизации - просто создаем уведомления
    
    deadline_count = create_deadline_notifications()
    overdue_count = create_overdue_notifications()
    
    return jsonify({
        'success': True,
        'message': 'Уведомления созданы',
        'data': {
            'deadline_notifications': deadline_count,
            'overdue_notifications': overdue_count
        }
    }), 200

