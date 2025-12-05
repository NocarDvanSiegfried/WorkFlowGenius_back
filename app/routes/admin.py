from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from datetime import datetime, timedelta
from app.database import db
from app.models import User, Task, AIRecommendation, PerformanceRecord, Assignment
from app.services.ml_service import ml_service
from app.services.performance_calculator import update_all_performance_records

admin_bp = Blueprint('admin', __name__)

@admin_bp.route('/system_health', methods=['GET'])
@jwt_required()
def system_health():
    """Проверка здоровья системы"""
    user_id = get_jwt_identity()
    current_user = User.query.get_or_404(user_id)
    
    if current_user.role not in ['manager', 'admin']:
        return jsonify({
            'success': False,
            'message': 'Недостаточно прав'
        }), 403
    
    # Статистика системы
    total_users = User.query.count()
    total_employees = User.query.filter_by(role='employee').count()
    total_managers = User.query.filter_by(role='manager').count()
    total_tasks = Task.query.count()
    total_recommendations = AIRecommendation.query.count()
    
    # Активные задачи
    active_tasks = Task.query.filter(
        Task.status.in_(['pending', 'assigned', 'in_progress'])
    ).count()
    
    # Просроченные задачи
    overdue_tasks = Task.query.filter(
        Task.deadline < datetime.utcnow(),
        Task.status.in_(['pending', 'assigned', 'in_progress'])
    ).count()
    
    # ML модель
    ml_status = {
        'loaded': ml_service.is_loaded,
        'model_path': ml_service.model_path if hasattr(ml_service, 'model_path') else None,
        'status': 'active' if ml_service.is_loaded else 'inactive'
    }
    
    # База данных
    try:
        db.session.execute('SELECT 1')
        db_status = 'connected'
    except:
        db_status = 'disconnected'
    
    return jsonify({
        'success': True,
        'data': {
            'system': {
                'status': 'operational',
                'timestamp': datetime.utcnow().isoformat(),
                'uptime': 'N/A'  # Можно добавить расчет
            },
            'users': {
                'total': total_users,
                'employees': total_employees,
                'managers': total_managers
            },
            'tasks': {
                'total': total_tasks,
                'active': active_tasks,
                'overdue': overdue_tasks,
                'pending': Task.query.filter_by(status='pending').count()
            },
            'ai': {
                'total_recommendations': total_recommendations,
                'pending_recommendations': AIRecommendation.query.filter_by(status='pending').count(),
                'accepted_recommendations': AIRecommendation.query.filter_by(status='accepted').count(),
                'acceptance_rate': (
                    AIRecommendation.query.filter_by(status='accepted').count() / 
                    total_recommendations * 100 if total_recommendations > 0 else 0
                )
            },
            'ml_service': ml_status,
            'database': {
                'status': db_status,
                'connection': 'sqlite'  # Можно определить тип БД
            },
            'performance': {
                'avg_response_time': 'N/A',
                'requests_per_minute': 'N/A'
            }
        }
    }), 200

@admin_bp.route('/ai_settings', methods=['GET'])
@jwt_required()
def ai_settings():
    """Настройки AI"""
    user_id = get_jwt_identity()
    current_user = User.query.get_or_404(user_id)
    
    if current_user.role not in ['manager', 'admin']:
        return jsonify({
            'success': False,
            'message': 'Недостаточно прав'
        }), 403
    
    return jsonify({
        'success': True,
        'data': {
            'ai_enabled': True,
            'model': {
                'name': 'XGBoost Regressor',
                'version': '2.0.3',
                'type': 'suitability_prediction'
            },
            'thresholds': {
                'suitability_threshold': 0.6,
                'confidence_threshold': 0.7,
                'workload_threshold': 0.8
            },
            'features': {
                'task_assignment_recommendations': True,
                'workload_optimization': True,
                'skill_matching': True,
                'performance_prediction': True
            },
            'auto_generation': {
                'enabled': True,
                'interval_hours': 24,
                'max_recommendations_per_run': 50
            },
            'ml_service': {
                'status': 'active' if ml_service.is_loaded else 'inactive',
                'model_loaded': ml_service.is_loaded
            }
        }
    }), 200

@admin_bp.route('/analytics', methods=['GET'])
@jwt_required()
def admin_analytics():
    """Аналитика для администратора"""
    user_id = get_jwt_identity()
    current_user = User.query.get_or_404(user_id)
    
    if current_user.role not in ['manager', 'admin']:
        return jsonify({
            'success': False,
            'message': 'Недостаточно прав'
        }), 403
    
    # Обновить записи производительности
    performance_results = update_all_performance_records()
    
    # Статистика за последнюю неделю
    week_ago = datetime.utcnow() - timedelta(days=7)
    
    # Задачи
    tasks_created_week = Task.query.filter(Task.created_at >= week_ago).count()
    tasks_completed_week = Task.query.filter(
        Task.status == 'completed',
        Task.updated_at >= week_ago
    ).count()
    
    # Назначения
    assignments_week = Assignment.query.filter(Assignment.assigned_at >= week_ago).count()
    
    # Рекомендации ИИ
    recommendations_week = AIRecommendation.query.filter(
        AIRecommendation.created_at >= week_ago
    ).count()
    
    accepted_recommendations = AIRecommendation.query.filter_by(status='accepted').count()
    total_recommendations = AIRecommendation.query.count()
    
    acceptance_rate = (
        accepted_recommendations / total_recommendations * 100 
        if total_recommendations > 0 else 0
    )
    
    # Производительность сотрудников
    employees = User.query.filter_by(role='employee').all()
    avg_efficiency = sum(e.efficiency_score for e in employees) / len(employees) if employees else 0
    avg_satisfaction = sum(e.satisfaction_score for e in employees) / len(employees) if employees else 0
    
    # Загруженность
    total_workload = sum(e.current_workload for e in employees)
    total_capacity = sum(e.max_workload for e in employees)
    avg_workload = (total_workload / total_capacity * 100) if total_capacity > 0 else 0
    
    return jsonify({
        'success': True,
        'data': {
            'period': {
                'start': week_ago.isoformat(),
                'end': datetime.utcnow().isoformat()
            },
            'tasks': {
                'created': tasks_created_week,
                'completed': tasks_completed_week,
                'completion_rate': (tasks_completed_week / tasks_created_week * 100) if tasks_created_week > 0 else 0,
                'active': Task.query.filter(Task.status.in_(['pending', 'assigned', 'in_progress'])).count()
            },
            'assignments': {
                'total': assignments_week,
                'completed': Assignment.query.filter_by(status='completed').count(),
                'in_progress': Assignment.query.filter_by(status='in_progress').count()
            },
            'ai_recommendations': {
                'total': total_recommendations,
                'this_week': recommendations_week,
                'accepted': accepted_recommendations,
                'acceptance_rate': round(acceptance_rate, 1),
                'pending': AIRecommendation.query.filter_by(status='pending').count()
            },
            'performance': {
                'employees_processed': len(performance_results),
                'avg_efficiency': round(avg_efficiency, 1),
                'avg_satisfaction': round(avg_satisfaction, 1),
                'avg_workload_percentage': round(avg_workload, 1),
                'overloaded_employees': len([e for e in employees if e.current_workload >= e.max_workload * 0.9])
            },
            'ml_model': {
                'used_for_recommendations': ml_service.is_loaded,
                'predictions_made': 'N/A'  # Можно добавить счетчик
            }
        }
    }), 200

@admin_bp.route('/teams', methods=['GET'])
@jwt_required()
def get_teams():
    """Получить информацию о командах"""
    user_id = get_jwt_identity()
    current_user = User.query.get_or_404(user_id)
    
    if current_user.role != 'manager':
        return jsonify({
            'success': False,
            'message': 'Недостаточно прав'
        }), 403
    
    employees = User.query.filter_by(role='employee').all()
    
    team_data = []
    for emp in employees:
        latest_perf = PerformanceRecord.query.filter_by(user_id=emp.id)\
            .order_by(PerformanceRecord.period_end.desc()).first()
        
        # Активные задачи сотрудника
        active_assignments = Assignment.query.filter_by(
            assigned_to=emp.id,
            status='in_progress'
        ).count()
        
        # Завершенные задачи за неделю
        week_ago = datetime.utcnow() - timedelta(days=7)
        completed_week = Assignment.query.filter(
            Assignment.assigned_to == emp.id,
            Assignment.status == 'completed',
            Assignment.completed_at >= week_ago
        ).count()
        
        team_data.append({
            'id': emp.id,
            'name': emp.name,
            'position': emp.position,
            'email': emp.email,
            'satisfaction': emp.satisfaction_score,
            'efficiency': emp.efficiency_score,
            'current_workload': emp.current_workload,
            'max_workload': emp.max_workload,
            'workload_percentage': (emp.current_workload / emp.max_workload * 100) if emp.max_workload > 0 else 0,
            'monthly_hours': emp.monthly_hours,
            'salary': emp.salary,
            'skills': [skill.skill_name for skill in emp.skills],
            'active_tasks': active_assignments,
            'completed_this_week': completed_week,
            'latest_performance': latest_perf.to_dict() if latest_perf else None,
            'ai_recommendations': AIRecommendation.query.filter_by(
                user_id=emp.id,
                status='pending'
            ).count()
        })
    
    # Сортировка по эффективности
    team_data.sort(key=lambda x: x['efficiency'], reverse=True)
    
    # Группировка по должностям
    positions = {}
    for emp in team_data:
        position = emp['position']
        if position not in positions:
            positions[position] = []
        positions[position].append(emp)
    
    return jsonify({
        'success': True,
        'data': {
            'team_members': team_data,
            'by_position': positions,
            'statistics': {
                'total_members': len(team_data),
                'positions_count': len(positions),
                'avg_efficiency': round(sum(e['efficiency'] for e in team_data) / len(team_data), 1) if team_data else 0,
                'avg_satisfaction': round(sum(e['satisfaction'] for e in team_data) / len(team_data), 1) if team_data else 0,
                'avg_workload_percentage': round(sum(e['workload_percentage'] for e in team_data) / len(team_data), 1) if team_data else 0,
                'total_active_tasks': sum(e['active_tasks'] for e in team_data),
                'total_completed_week': sum(e['completed_this_week'] for e in team_data)
            }
        }
    }), 200

@admin_bp.route('/create_task', methods=['POST'])
@jwt_required()
def admin_create_task():
    """Создать задачу через админку"""
    user_id = get_jwt_identity()
    current_user = User.query.get_or_404(user_id)
    
    if current_user.role != 'manager':
        return jsonify({
            'success': False,
            'message': 'Недостаточно прав'
        }), 403
    
    data = request.json
    
    if not data or 'title' not in data:
        return jsonify({
            'success': False,
            'message': 'Отсутствует заголовок задачи'
        }), 400
    
    # Создание задачи
    task = Task(
        title=data['title'],
        description=data.get('description'),
        priority=data.get('priority', 'medium'),
        estimated_hours=data.get('estimated_hours'),
        created_by=user_id,
        deadline=data.get('deadline')
    )
    
    db.session.add(task)
    db.session.flush()
    
    # Автоматическое назначение если указано
    if data.get('auto_assign', True):
        from app.services.task_distributor import assign_task_automatically
        assignment = assign_task_automatically(task.id, user_id)
        
        if assignment:
            task.status = 'assigned'
    
    db.session.commit()
    
    return jsonify({
        'success': True,
        'data': task.to_dict(),
        'message': 'Задача успешно создана'
    }), 201

@admin_bp.route('/update_ml_model', methods=['POST'])
@jwt_required()
def update_ml_model():
    """Обновить ML модель"""
    user_id = get_jwt_identity()
    current_user = User.query.get_or_404(user_id)
    
    if current_user.role != 'admin':
        return jsonify({
            'success': False,
            'message': 'Недостаточно прав'
        }), 403
    
    data = request.json
    model_path = data.get('model_path')
    
    if model_path:
        ml_service.model_path = model_path
    
    success = ml_service.load_model()
    
    return jsonify({
        'success': success,
        'message': 'ML модель обновлена' if success else 'Ошибка обновления ML модели',
        'model_loaded': ml_service.is_loaded,
        'model_path': ml_service.model_path
    }), 200 if success else 500