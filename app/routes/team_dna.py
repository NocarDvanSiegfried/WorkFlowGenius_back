"""
API endpoints для командного ДНК (Team DNA)
"""
from flask import Blueprint, request, jsonify

from app.database import db
from app.models import User, TeamConnection
from app.services.team_dna_analyzer import (
    calculate_connection_strength,
    get_strong_connections,
    find_hidden_experts,
    calculate_team_synergy,
    find_dream_teams
)

team_dna_bp = Blueprint('team_dna', __name__)


@team_dna_bp.route('/stats', methods=['GET'])
def get_team_dna_stats():
    """Получить статистику командного ДНК"""
    # Без авторизации - просто возвращаем статистику
    
    # Сильные связи (>= 0.7)
    all_connections = TeamConnection.query.filter(
        TeamConnection.connection_strength >= 0.7
    ).count()
    
    # Скрытые эксперты
    hidden_experts = find_hidden_experts()
    
    # Синергия команды (средняя по всем парам)
    employees = User.query.filter_by(role='employee').all()
    employee_ids = [e.id for e in employees]
    team_synergy = calculate_team_synergy(employee_ids) if len(employee_ids) >= 2 else 0.0
    
    # Dream teams
    dream_teams = find_dream_teams(min_synergy=8.0)
    
    return jsonify({
        'success': True,
        'data': {
            'strong_connections': all_connections,
            'hidden_experts': len(hidden_experts),
            'team_synergy': round(team_synergy, 1),
            'dream_teams': len(dream_teams),
        }
    }), 200


@team_dna_bp.route('/connections', methods=['GET'])
def get_connections():
    """Получить граф связей команды"""
    # Без авторизации - просто возвращаем связи
    
    # Получить все связи
    connections = TeamConnection.query.all()
    
    # Получить всех сотрудников
    employees = User.query.filter_by(role='employee').all()
    
    nodes = []
    edges = []
    
    # Создаем узлы (сотрудники)
    for emp in employees:
        nodes.append({
            'id': str(emp.id),
            'name': emp.name,
            'role': emp.role,
            'efficiency': emp.efficiency,
        })
    
    # Создаем ребра (связи)
    for conn in connections:
        edges.append({
            'source': str(conn.user1_id),
            'target': str(conn.user2_id),
            'strength': float(conn.connection_strength),
            'type': conn.connection_type,
        })
    
    return jsonify({
        'success': True,
        'data': {
            'nodes': nodes,
            'edges': edges,
        }
    }), 200


@team_dna_bp.route('/connections/<int:user_id>', methods=['GET'])
def get_user_connections(user_id):
    """Получить связи конкретного пользователя"""
    # Без авторизации - просто возвращаем связи пользователя
    
    connections = TeamConnection.query.filter(
        ((TeamConnection.user1_id == user_id) | (TeamConnection.user2_id == user_id)) &
        (TeamConnection.connection_strength >= 0.3)
    ).all()
    
    result = []
    for conn in connections:
        other_user_id = conn.user2_id if conn.user1_id == user_id else conn.user1_id
        other_user = User.query.get(other_user_id)
        result.append({
            'user1_id': conn.user1_id,
            'user2_id': conn.user2_id,
            'user1_name': User.query.get(conn.user1_id).name if User.query.get(conn.user1_id) else f'User {conn.user1_id}',
            'user2_name': User.query.get(conn.user2_id).name if User.query.get(conn.user2_id) else f'User {conn.user2_id}',
            'connection_strength': float(conn.connection_strength),
            'connection_type': conn.connection_type,
            'synergy_score': float(conn.synergy_score) if conn.synergy_score else 0.0,
        })
    
    return jsonify({
        'success': True,
        'data': result
    }), 200


@team_dna_bp.route('/hidden-experts', methods=['GET'])
def get_hidden_experts():
    """Получить список скрытых экспертов"""
    # Без авторизации - просто возвращаем скрытых экспертов
    
    hidden_experts = find_hidden_experts()
    
    return jsonify({
        'success': True,
        'data': hidden_experts
    }), 200


@team_dna_bp.route('/dream-teams', methods=['GET'])
def get_dream_teams():
    """Получить оптимальные команды (dream teams)"""
    # Без авторизации - просто возвращаем dream teams
    
    min_synergy = float(request.args.get('min_synergy', 8.0))
    dream_teams = find_dream_teams(min_synergy=min_synergy)
    
    return jsonify({
        'success': True,
        'data': dream_teams
    }), 200


@team_dna_bp.route('/synergy', methods=['POST'])
def calculate_synergy():
    """Рассчитать синергию для указанной команды"""
    # Без авторизации - просто рассчитываем синергию
    
    if not request.json or 'team_user_ids' not in request.json:
        return jsonify({
            'success': False,
            'message': 'Не указаны ID пользователей команды'
        }), 400
    
    team_user_ids = request.json['team_user_ids']
    
    if not isinstance(team_user_ids, list) or len(team_user_ids) < 2:
        return jsonify({
            'success': False,
            'message': 'Команда должна содержать минимум 2 человека'
        }), 400
    
    synergy = calculate_team_synergy(team_user_ids)
    
    return jsonify({
        'success': True,
        'data': {
            'synergy': synergy,
            'team_size': len(team_user_ids),
        }
    }), 200

