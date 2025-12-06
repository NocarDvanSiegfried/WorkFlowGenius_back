from datetime import datetime
from app.database import db

class User(db.Model):
    """Модель пользователя"""
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(255), unique=True, nullable=False, index=True)
    name = db.Column(db.String(255), nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    role = db.Column(db.String(50), nullable=False, default='employee')  # manager, employee
    current_workload = db.Column(db.Integer, default=0)
    max_workload = db.Column(db.Integer, default=100)
    satisfaction = db.Column(db.Integer, default=7)  # Удовлетворенность 1-10
    efficiency = db.Column(db.Integer, default=100)  # Эффективность работы (%)
    avg_hours_per_month = db.Column(db.Integer, default=160)  # Среднее кол-во рабочих часов в месяц
    salary = db.Column(db.String(50))  # Зарплата
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Связи
    created_tasks = db.relationship('Task', backref='creator', lazy=True, foreign_keys='Task.created_by', cascade='all, delete-orphan')
    assignments = db.relationship('Assignment', backref='user', lazy=True, foreign_keys='Assignment.assigned_to')
    competencies = db.relationship('UserCompetency', backref='user', lazy=True, cascade='all, delete-orphan')
    work_preferences = db.relationship('WorkPreference', backref='user', lazy=True, uselist=False, cascade='all, delete-orphan')
    team_connections = db.relationship('TeamConnection', foreign_keys='TeamConnection.user1_id', backref='user1', lazy=True)
    team_connections_reverse = db.relationship('TeamConnection', foreign_keys='TeamConnection.user2_id', backref='user2', lazy=True)
    
    def to_dict(self):
        return {
            'id': self.id,
            'email': self.email,
            'name': self.name,
            'role': self.role,
            'current_workload': self.current_workload,
            'max_workload': self.max_workload,
            'satisfaction': self.satisfaction,
            'efficiency': self.efficiency,
            'avg_hours_per_month': self.avg_hours_per_month,
            'salary': self.salary,
            'created_at': self.created_at.isoformat() if self.created_at else None,
        }

class Task(db.Model):
    """Модель задачи"""
    __tablename__ = 'tasks'
    
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(255), nullable=False)
    description = db.Column(db.Text)
    priority = db.Column(db.String(20), nullable=False, default='medium')  # low, medium, high, urgent
    status = db.Column(db.String(20), default='pending', index=True)  # pending, assigned, in_progress, completed, cancelled
    deadline = db.Column(db.DateTime)
    estimated_hours = db.Column(db.Float)
    required_competencies = db.Column(db.JSON, default=[])  # Например, ['Python', 'SQL']
    created_by = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Связи
    assignments = db.relationship('Assignment', backref='task', lazy=True, cascade='all, delete-orphan')
    comments = db.relationship('TaskComment', backref='task', lazy=True, cascade='all, delete-orphan', order_by='TaskComment.created_at.desc()')
    tags = db.relationship('TaskTag', backref='task', lazy=True, cascade='all, delete-orphan')
    time_tracking_entries = db.relationship('TimeTracking', backref='task', lazy=True, cascade='all, delete-orphan')
    history = db.relationship('TaskHistory', backref='task', lazy=True, cascade='all, delete-orphan', order_by='TaskHistory.created_at.desc()')
    rating = db.Column(db.Integer)  # Оценка выполнения задачи (1-5)
    
    def to_dict(self):
        return {
            'id': self.id,
            'title': self.title,
            'description': self.description,
            'priority': self.priority,
            'status': self.status,
            'deadline': self.deadline.isoformat() if self.deadline else None,
            'estimated_hours': float(self.estimated_hours) if self.estimated_hours else None,
            'created_by': self.created_by,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
            'rating': self.rating,
            'required_competencies': self.required_competencies or [],
            'tags': [tag.to_dict() for tag in self.tags],
        }

class Assignment(db.Model):
    """Модель назначения задачи"""
    __tablename__ = 'assignments'
    
    id = db.Column(db.Integer, primary_key=True)
    task_id = db.Column(db.Integer, db.ForeignKey('tasks.id', ondelete='CASCADE'), nullable=False)
    assigned_to = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    assigned_by = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    assigned_at = db.Column(db.DateTime, default=datetime.utcnow)
    status = db.Column(db.String(20), default='assigned', index=True)  # assigned, in_progress, completed, cancelled
    workload_points = db.Column(db.Integer, nullable=False, default=10)
    completed_at = db.Column(db.DateTime)
    suitability_score = db.Column(db.Float)  # Оценка пригодности сотрудника для задачи (0-1)
    
    def to_dict(self):
        return {
            'id': self.id,
            'task_id': self.task_id,
            'assigned_to': self.assigned_to,
            'assigned_by': self.assigned_by,
            'assigned_at': self.assigned_at.isoformat() if self.assigned_at else None,
            'status': self.status,
            'workload_points': self.workload_points,
            'completed_at': self.completed_at.isoformat() if self.completed_at else None,
            'suitability_score': float(self.suitability_score) if self.suitability_score else None,
        }

class UserCompetency(db.Model):
    """Модель компетенций пользователя"""
    __tablename__ = 'user_competencies'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='CASCADE'), nullable=False, index=True)
    skill_name = db.Column(db.String(100), nullable=False)  # Python, React, UI/UX и т.д.
    experience_years = db.Column(db.Float, default=0)  # Опыт в годах
    level = db.Column(db.String(20), default='intermediate')  # beginner, intermediate, advanced, expert
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def to_dict(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'skill_name': self.skill_name,
            'experience_years': float(self.experience_years),
            'level': self.level,
        }

class WorkPreference(db.Model):
    """Модель предпочтений времени работы"""
    __tablename__ = 'work_preferences'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='CASCADE'), nullable=False, unique=True, index=True)
    preferred_start_time = db.Column(db.String(10))  # "09:00"
    preferred_end_time = db.Column(db.String(10))  # "18:00"
    preferred_days = db.Column(db.String(50))  # "monday,tuesday,wednesday,thursday,friday"
    timezone = db.Column(db.String(50), default='UTC')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def to_dict(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'preferred_start_time': self.preferred_start_time,
            'preferred_end_time': self.preferred_end_time,
            'preferred_days': self.preferred_days.split(',') if self.preferred_days else [],
            'timezone': self.timezone,
        }

class TeamConnection(db.Model):
    """Модель связей между сотрудниками (для Team DNA)"""
    __tablename__ = 'team_connections'
    
    id = db.Column(db.Integer, primary_key=True)
    user1_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='CASCADE'), nullable=False, index=True)
    user2_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='CASCADE'), nullable=False, index=True)
    connection_strength = db.Column(db.Float, default=0.5)  # 0-1, сила связи
    connection_type = db.Column(db.String(20), default='normal')  # strong, normal, weak, hidden_talent
    projects_together = db.Column(db.Integer, default=0)  # Количество совместных проектов
    tasks_together = db.Column(db.Integer, default=0)  # Количество совместных задач
    synergy_score = db.Column(db.Float)  # Оценка синергии
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def to_dict(self):
        return {
            'id': self.id,
            'user1_id': self.user1_id,
            'user2_id': self.user2_id,
            'connection_strength': float(self.connection_strength),
            'connection_type': self.connection_type,
            'projects_together': self.projects_together,
            'tasks_together': self.tasks_together,
            'synergy_score': float(self.synergy_score) if self.synergy_score else None,
        }

class AISettings(db.Model):
    """Модель настроек ИИ алгоритма"""
    __tablename__ = 'ai_settings'
    
    id = db.Column(db.Integer, primary_key=True)
    competence_weight = db.Column(db.Integer, default=85)  # Вес учета компетенций (0-100)
    load_weight = db.Column(db.Integer, default=90)  # Вес анализа загруженности (0-100)
    time_preference_weight = db.Column(db.Integer, default=70)  # Вес предпочтений времени (0-100)
    priority_weight = db.Column(db.Integer, default=95)  # Вес оптимизации по приоритетам (0-100)
    auto_balance_enabled = db.Column(db.Boolean, default=True)
    predict_completion_enabled = db.Column(db.Boolean, default=True)
    smart_recommendations_enabled = db.Column(db.Boolean, default=True)
    continuous_learning_enabled = db.Column(db.Boolean, default=True)
    anonymization_enabled = db.Column(db.Boolean, default=True)
    model_update_frequency = db.Column(db.String(20), default='daily')  # daily, weekly, monthly
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def to_dict(self):
        return {
            'id': self.id,
            'competence_weight': self.competence_weight,
            'load_weight': self.load_weight,
            'time_preference_weight': self.time_preference_weight,
            'priority_weight': self.priority_weight,
            'auto_balance_enabled': self.auto_balance_enabled,
            'predict_completion_enabled': self.predict_completion_enabled,
            'smart_recommendations_enabled': self.smart_recommendations_enabled,
            'continuous_learning_enabled': self.continuous_learning_enabled,
            'anonymization_enabled': self.anonymization_enabled,
            'model_update_frequency': self.model_update_frequency,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
        }

class ModelMetrics(db.Model):
    """Модель метрик ИИ модели"""
    __tablename__ = 'model_metrics'
    
    id = db.Column(db.Integer, primary_key=True)
    training_examples = db.Column(db.Integer, default=0)
    accuracy = db.Column(db.Float)  # Точность модели (%)
    f1_score = db.Column(db.Float)  # F1-score
    training_time_minutes = db.Column(db.Float)  # Время обучения в минутах
    last_training_date = db.Column(db.DateTime)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def to_dict(self):
        return {
            'id': self.id,
            'training_examples': self.training_examples,
            'accuracy': float(self.accuracy) if self.accuracy else None,
            'f1_score': float(self.f1_score) if self.f1_score else None,
            'training_time_minutes': float(self.training_time_minutes) if self.training_time_minutes else None,
            'last_training_date': self.last_training_date.isoformat() if self.last_training_date else None,
        }

class TaskComment(db.Model):
    """Модель комментариев к задачам"""
    __tablename__ = 'task_comments'
    
    id = db.Column(db.Integer, primary_key=True)
    task_id = db.Column(db.Integer, db.ForeignKey('tasks.id', ondelete='CASCADE'), nullable=False, index=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    content = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Связи
    user = db.relationship('User', backref='task_comments', lazy=True)
    
    def to_dict(self):
        return {
            'id': self.id,
            'task_id': self.task_id,
            'user_id': self.user_id,
            'user': self.user.to_dict() if self.user else None,
            'content': self.content,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
        }

class Notification(db.Model):
    """Модель уведомлений"""
    __tablename__ = 'notifications'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='CASCADE'), nullable=False, index=True)
    type = db.Column(db.String(50), nullable=False)  # task_assigned, task_completed, deadline_approaching, comment_added, etc.
    title = db.Column(db.String(255), nullable=False)
    message = db.Column(db.Text)
    related_task_id = db.Column(db.Integer, db.ForeignKey('tasks.id', ondelete='CASCADE'), nullable=True)
    is_read = db.Column(db.Boolean, default=False, index=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, index=True)
    
    # Связи
    user = db.relationship('User', backref='notifications', lazy=True)
    related_task = db.relationship('Task', backref='notifications', lazy=True)
    
    def to_dict(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'type': self.type,
            'title': self.title,
            'message': self.message,
            'related_task_id': self.related_task_id,
            'is_read': self.is_read,
            'created_at': self.created_at.isoformat() if self.created_at else None,
        }

class TaskHistory(db.Model):
    """Модель истории изменений задач"""
    __tablename__ = 'task_history'
    
    id = db.Column(db.Integer, primary_key=True)
    task_id = db.Column(db.Integer, db.ForeignKey('tasks.id', ondelete='CASCADE'), nullable=False, index=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    action = db.Column(db.String(50), nullable=False)  # created, updated, status_changed, assigned, etc.
    field_name = db.Column(db.String(50))  # Название измененного поля
    old_value = db.Column(db.Text)  # Старое значение
    new_value = db.Column(db.Text)  # Новое значение
    created_at = db.Column(db.DateTime, default=datetime.utcnow, index=True)
    
    # Связи
    user = db.relationship('User', backref='task_history_entries', lazy=True)
    
    def to_dict(self):
        return {
            'id': self.id,
            'task_id': self.task_id,
            'user_id': self.user_id,
            'user': self.user.to_dict() if self.user else None,
            'action': self.action,
            'field_name': self.field_name,
            'old_value': self.old_value,
            'new_value': self.new_value,
            'created_at': self.created_at.isoformat() if self.created_at else None,
        }

class TaskTag(db.Model):
    """Модель тегов задач"""
    __tablename__ = 'task_tags'
    
    id = db.Column(db.Integer, primary_key=True)
    task_id = db.Column(db.Integer, db.ForeignKey('tasks.id', ondelete='CASCADE'), nullable=False, index=True)
    tag_name = db.Column(db.String(50), nullable=False)
    color = db.Column(db.String(20), default='blue')  # Цвет тега для UI
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def to_dict(self):
        return {
            'id': self.id,
            'task_id': self.task_id,
            'tag_name': self.tag_name,
            'color': self.color,
        }

class TimeTracking(db.Model):
    """Модель отслеживания времени работы над задачами"""
    __tablename__ = 'time_tracking'
    
    id = db.Column(db.Integer, primary_key=True)
    task_id = db.Column(db.Integer, db.ForeignKey('tasks.id', ondelete='CASCADE'), nullable=False, index=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    start_time = db.Column(db.DateTime, nullable=False)
    end_time = db.Column(db.DateTime)
    duration_minutes = db.Column(db.Integer)  # Длительность в минутах
    description = db.Column(db.Text)  # Описание работы
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Связи
    user = db.relationship('User', backref='time_tracking_entries', lazy=True)
    
    def to_dict(self):
        return {
            'id': self.id,
            'task_id': self.task_id,
            'user_id': self.user_id,
            'user': self.user.to_dict() if self.user else None,
            'start_time': self.start_time.isoformat() if self.start_time else None,
            'end_time': self.end_time.isoformat() if self.end_time else None,
            'duration_minutes': self.duration_minutes,
            'description': self.description,
            'created_at': self.created_at.isoformat() if self.created_at else None,
        }

