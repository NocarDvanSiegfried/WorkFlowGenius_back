"""
Сервис анализа командного ДНК (Team DNA)
Анализ связей между сотрудниками и формирование оптимальных команд
"""
from app.database import db
from app.models import User, TeamConnection, Assignment, Task


def calculate_connection_strength(user1_id, user2_id):
    """
    Рассчитать силу связи между двумя сотрудниками
    
    Args:
        user1_id: ID первого сотрудника
        user2_id: ID второго сотрудника
    
    Returns:
        float: Сила связи (0-1)
    """
    # Проверяем существующую связь
    connection = TeamConnection.query.filter(
        ((TeamConnection.user1_id == user1_id) & (TeamConnection.user2_id == user2_id)) |
        ((TeamConnection.user1_id == user2_id) & (TeamConnection.user2_id == user1_id))
    ).first()
    
    if connection:
        return float(connection.connection_strength)
    
    # Рассчитываем на основе совместных задач
    user1_task_ids = [
        row[0] for row in Assignment.query.filter_by(assigned_to=user1_id, status='completed')
        .with_entities(Assignment.task_id).all()
    ]
    user2_task_ids = [
        row[0] for row in Assignment.query.filter_by(assigned_to=user2_id, status='completed')
        .with_entities(Assignment.task_id).all()
    ]
    
    user1_tasks_set = set(user1_task_ids)
    user2_tasks_set = set(user2_task_ids)
    
    common_tasks = len(user1_tasks_set & user2_tasks_set)
    total_tasks = len(user1_tasks_set | user2_tasks_set)
    
    if total_tasks == 0:
        return 0.0
    
    # Базовая сила связи на основе совместных задач
    base_strength = min(common_tasks / max(total_tasks, 1), 1.0)
    
    # Сохраняем связь
    if connection is None:
        connection = TeamConnection(
            user1_id=min(user1_id, user2_id),
            user2_id=max(user1_id, user2_id),
            connection_strength=base_strength,
            tasks_together=common_tasks
        )
        db.session.add(connection)
        db.session.commit()
    
    return base_strength


def get_strong_connections(user_id, threshold=0.7):
    """
    Получить сильные связи пользователя
    
    Args:
        user_id: ID пользователя
        threshold: Порог силы связи (0-1)
    
    Returns:
        list: Список связей с силой >= threshold
    """
    connections = TeamConnection.query.filter(
        ((TeamConnection.user1_id == user_id) | (TeamConnection.user2_id == user_id)) &
        (TeamConnection.connection_strength >= threshold)
    ).all()
    
    result = []
    for conn in connections:
        other_user_id = conn.user2_id if conn.user1_id == user_id else conn.user1_id
        result.append({
            'user_id': other_user_id,
            'connection_strength': float(conn.connection_strength),
            'connection_type': conn.connection_type,
            'tasks_together': conn.tasks_together,
        })
    
    return result


def find_hidden_experts():
    """
    Найти скрытых экспертов (сотрудников с высокой эффективностью,
    но низкой видимостью в команде)
    
    Returns:
        list: Список скрытых экспертов
    """
    users = User.query.filter_by(role='employee').all()
    hidden_experts = []
    
    for user in users:
        # Высокая эффективность (>150%)
        if user.efficiency > 150:
            # Низкое количество связей
            connections_count = TeamConnection.query.filter(
                ((TeamConnection.user1_id == user.id) | (TeamConnection.user2_id == user.id))
            ).count()
            
            if connections_count < 3:  # Мало связей
                hidden_experts.append({
                    'user_id': user.id,
                    'name': user.name,
                    'efficiency': user.efficiency,
                    'connections_count': connections_count,
                })
    
    return hidden_experts


def calculate_team_synergy(team_user_ids):
    """
    Рассчитать синергию команды
    
    Args:
        team_user_ids: Список ID пользователей в команде
    
    Returns:
        float: Оценка синергии (0-10)
    """
    if len(team_user_ids) < 2:
        return 5.0
    
    total_strength = 0.0
    pairs_count = 0
    
    # Рассчитываем среднюю силу связей между всеми парами
    for i, user1_id in enumerate(team_user_ids):
        for user2_id in team_user_ids[i+1:]:
            strength = calculate_connection_strength(user1_id, user2_id)
            total_strength += strength
            pairs_count += 1
    
    if pairs_count == 0:
        return 5.0
    
    avg_strength = total_strength / pairs_count
    
    # Преобразуем в шкалу 0-10
    synergy_score = avg_strength * 10.0
    
    return round(synergy_score, 1)


def find_dream_teams(min_team_size=2, max_team_size=5, min_synergy=8.0):
    """
    Найти оптимальные команды (dream teams)
    
    Args:
        min_team_size: Минимальный размер команды
        max_team_size: Максимальный размер команды
        min_synergy: Минимальная синергия
    
    Returns:
        list: Список оптимальных команд
    """
    users = User.query.filter_by(role='employee').all()
    user_ids = [u.id for u in users]
    
    if len(user_ids) < min_team_size:
        return []
    
    dream_teams = []
    
    # Простой алгоритм: проверяем комбинации пользователей
    from itertools import combinations
    
    for team_size in range(min_team_size, min(max_team_size + 1, len(user_ids) + 1)):
        for team in combinations(user_ids, team_size):
            synergy = calculate_team_synergy(list(team))
            
            if synergy >= min_synergy:
                team_users = [User.query.get(uid) for uid in team]
                dream_teams.append({
                    'team': [{'id': u.id, 'name': u.name} for u in team_users],
                    'synergy': synergy,
                    'size': len(team),
                })
    
    # Сортируем по синергии
    dream_teams.sort(key=lambda x: x['synergy'], reverse=True)
    
    return dream_teams[:5]  # Возвращаем топ-5 команд

