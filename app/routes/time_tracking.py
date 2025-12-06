from flask import Blueprint, request, jsonify

from datetime import datetime, timedelta
from app.database import db
from app.models import Task, TimeTracking, User

time_tracking_bp = Blueprint('time_tracking', __name__)

@time_tracking_bp.route('/tasks/<int:task_id>/time-tracking', methods=['GET'])
def get_task_time_tracking(task_id):
    """Получить записи отслеживания времени для задачи"""
    task = Task.query.get_or_404(task_id)
    
    entries = TimeTracking.query.filter_by(task_id=task_id).order_by(TimeTracking.created_at.desc()).all()
    
    total_minutes = sum(entry.duration_minutes or 0 for entry in entries)
    
    return jsonify({
        'success': True,
        'data': {
            'data': [entry.to_dict() for entry in entries],
            'total_minutes': total_minutes
        }
    }), 200

@time_tracking_bp.route('/tasks/<int:task_id>/time-tracking/start', methods=['POST'])
def start_time_tracking(task_id):
    """Начать отслеживание времени"""
    task = Task.query.get_or_404(task_id)
    # Без авторизации - берем первого сотрудника
    user = User.query.filter_by(role='employee').first()
    user_id = user.id if user else 1
    
    # Проверка: есть ли активное отслеживание?
    active_entry = TimeTracking.query.filter_by(
        task_id=task_id,
        user_id=user_id,
        end_time=None
    ).first()
    
    if active_entry:
        return jsonify({
            'success': False,
            'message': 'Уже есть активное отслеживание времени для этой задачи'
        }), 400
    
    entry = TimeTracking(
        task_id=task_id,
        user_id=user_id,
        start_time=datetime.utcnow()
    )
    
    db.session.add(entry)
    db.session.commit()
    
    return jsonify({
        'success': True,
        'data': entry.to_dict(),
        'message': 'Отслеживание времени начато'
    }), 201

@time_tracking_bp.route('/tasks/<int:task_id>/time-tracking/stop', methods=['POST'])
def stop_time_tracking(task_id):
    """Остановить отслеживание времени"""
    # Без авторизации - берем первого сотрудника
    user = User.query.filter_by(role='employee').first()
    user_id = user.id if user else 1
    
    entry = TimeTracking.query.filter_by(
        task_id=task_id,
        user_id=user_id,
        end_time=None
    ).first()
    
    if not entry:
        return jsonify({
            'success': False,
            'message': 'Нет активного отслеживания времени'
        }), 400
    
    entry.end_time = datetime.utcnow()
    
    # Вычисляем длительность
    if entry.start_time:
        duration = entry.end_time - entry.start_time
        entry.duration_minutes = int(duration.total_seconds() / 60)
    
    db.session.commit()
    
    return jsonify({
        'success': True,
        'data': entry.to_dict(),
        'message': 'Отслеживание времени остановлено'
    }), 200

@time_tracking_bp.route('/time-tracking/<int:entry_id>', methods=['PUT'])
def update_time_tracking_entry(entry_id):
    """Обновить запись отслеживания времени"""
    entry = TimeTracking.query.get_or_404(entry_id)
    # Без авторизации - разрешаем обновление
    
    if not request.json:
        return jsonify({
            'success': False,
            'message': 'Отсутствуют данные'
        }), 400
    
    data = request.json
    
    if 'description' in data:
        entry.description = data['description']
    
    if 'duration_minutes' in data:
        entry.duration_minutes = data['duration_minutes']
    
    if 'start_time' in data:
        try:
            entry.start_time = datetime.fromisoformat(data['start_time'].replace('Z', '+00:00'))
        except (ValueError, AttributeError):
            pass
    
    if 'end_time' in data:
        try:
            entry.end_time = datetime.fromisoformat(data['end_time'].replace('Z', '+00:00'))
        except (ValueError, AttributeError):
            pass
    
    db.session.commit()
    
    return jsonify({
        'success': True,
        'data': entry.to_dict(),
        'message': 'Запись успешно обновлена'
    }), 200

@time_tracking_bp.route('/time-tracking/<int:entry_id>', methods=['DELETE'])
def delete_time_tracking_entry(entry_id):
    """Удалить запись отслеживания времени"""
    entry = TimeTracking.query.get_or_404(entry_id)
    # Без авторизации - разрешаем удаление
    
    db.session.delete(entry)
    db.session.commit()
    
    return jsonify({
        'success': True,
        'message': 'Запись успешно удалена'
    }), 200

