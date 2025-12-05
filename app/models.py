# models.py - ПОЛНАЯ ИСПРАВЛЕННАЯ ВЕРСИЯ
from datetime import datetime
from app.database import db

# ==================== ОСНОВНЫЕ МОДЕЛИ ====================

class User(db.Model):
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(255), unique=True, nullable=False, index=True)
    name = db.Column(db.String(255), nullable=False)
    position = db.Column(db.String(255))
    password_hash = db.Column(db.String(255), nullable=False)
    role = db.Column(db.String(50), nullable=False, default='employee')
    current_workload = db.Column(db.Integer, default=0)
    max_workload = db.Column(db.Integer, default=100)
    satisfaction_score = db.Column(db.Integer, default=7)
    efficiency_score = db.Column(db.Integer, default=8)
    monthly_hours = db.Column(db.Integer, default=160)
    salary = db.Column(db.Integer)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Связи (исправленные)
    skills = db.relationship('UserSkill', backref='user', lazy=True, cascade='all, delete-orphan')
    performance_records = db.relationship('PerformanceRecord', backref='user', lazy=True, cascade='all, delete-orphan')
    created_tasks = db.relationship('Task', backref='creator', lazy=True, foreign_keys='Task.created_by')
    assignments = db.relationship('Assignment', backref='assignee', lazy=True, foreign_keys='Assignment.assigned_to')
    recommendations = db.relationship('AIRecommendation', backref='user', lazy=True, foreign_keys='AIRecommendation.user_id')
    
    def to_dict(self):
        return {
            'id': self.id,
            'email': self.email,
            'name': self.name,
            'position': self.position,
            'role': self.role,
            'current_workload': self.current_workload,
            'max_workload': self.max_workload,
            'workload_percentage': (self.current_workload / self.max_workload * 100) if self.max_workload > 0 else 0,
            'satisfaction_score': self.satisfaction_score,
            'efficiency_score': self.efficiency_score,
            'monthly_hours': self.monthly_hours,
            'salary': self.salary,
            'skills': [skill.skill_name for skill in self.skills] if self.skills else [],
            'created_at': self.created_at.isoformat() if self.created_at else None,
        }

class Task(db.Model):
    """Модель задачи - ОРИГИНАЛЬНАЯ"""
    __tablename__ = 'tasks'
    
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(255), nullable=False)
    description = db.Column(db.Text)
    priority = db.Column(db.String(20), nullable=False, default='medium')  # low, medium, high, urgent
    status = db.Column(db.String(20), default='pending', index=True)  # pending, assigned, in_progress, completed, cancelled
    deadline = db.Column(db.DateTime)
    estimated_hours = db.Column(db.Float)
    created_by = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Связи
    assignments = db.relationship('Assignment', backref='task', lazy=True, cascade='all, delete-orphan')
    recommendations = db.relationship('AIRecommendation', backref='task', lazy=True, foreign_keys='AIRecommendation.task_id')
    
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
        }

class Assignment(db.Model):
    """Модель назначения задачи - ОРИГИНАЛЬНАЯ"""
    __tablename__ = 'assignments'
    
    id = db.Column(db.Integer, primary_key=True)
    task_id = db.Column(db.Integer, db.ForeignKey('tasks.id', ondelete='CASCADE'), nullable=False)
    assigned_to = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    assigned_by = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    assigned_at = db.Column(db.DateTime, default=datetime.utcnow)
    status = db.Column(db.String(20), default='assigned', index=True)  # assigned, in_progress, completed, cancelled
    workload_points = db.Column(db.Integer, nullable=False, default=10)
    completed_at = db.Column(db.DateTime)
    
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
        }

# ==================== НОВЫЕ МОДЕЛИ ====================

class Skill(db.Model):
    """Модель навыка/компетенции"""
    __tablename__ = 'skills'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), unique=True, nullable=False)
    category = db.Column(db.String(50))  # programming, design, management, etc.
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Связи
    user_skills = db.relationship('UserSkill', backref='skill', lazy=True, cascade='all, delete-orphan')
    
    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'category': self.category,
        }

class UserSkill(db.Model):
    """Связь пользователя и навыка"""
    __tablename__ = 'user_skills'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='CASCADE'), nullable=False)
    skill_id = db.Column(db.Integer, db.ForeignKey('skills.id', ondelete='CASCADE'), nullable=False)
    proficiency = db.Column(db.Integer, default=5)  # Уровень владения 1-10
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Для удобства
    skill_name = db.Column(db.String(100))  # Дублируем для быстрого доступа
    
    __table_args__ = (
        db.UniqueConstraint('user_id', 'skill_id', name='unique_user_skill'),
    )

class Team(db.Model):
    """Модель команды/отдела"""
    __tablename__ = 'teams'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255), nullable=False)
    description = db.Column(db.Text)
    manager_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Связи
    members = db.relationship('TeamMember', backref='team', lazy=True, cascade='all, delete-orphan')
    
    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'description': self.description,
            'manager_id': self.manager_id,
            'member_count': len(self.members),
            'created_at': self.created_at.isoformat() if self.created_at else None,
        }

class TeamMember(db.Model):
    """Связь команды и пользователя"""
    __tablename__ = 'team_members'
    
    id = db.Column(db.Integer, primary_key=True)
    team_id = db.Column(db.Integer, db.ForeignKey('teams.id', ondelete='CASCADE'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='CASCADE'), nullable=False)
    role = db.Column(db.String(50), default='member')  # member, lead, etc.
    joined_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    __table_args__ = (
        db.UniqueConstraint('team_id', 'user_id', name='unique_team_member'),
    )

class PerformanceRecord(db.Model):
    """Запись о производительности сотрудника"""
    __tablename__ = 'performance_records'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='CASCADE'), nullable=False)
    period_start = db.Column(db.Date, nullable=False)  # Начало периода (неделя/месяц)
    period_end = db.Column(db.Date, nullable=False)    # Конец периода
    tasks_completed = db.Column(db.Integer, default=0)
    tasks_on_time = db.Column(db.Integer, default=0)
    total_hours = db.Column(db.Float, default=0.0)
    quality_score = db.Column(db.Float, default=0.0)   # Оценка качества 0-100
    efficiency_score = db.Column(db.Float, default=0.0) # Оценка эффективности 0-100
    workload_percentage = db.Column(db.Float, default=0.0)
    rating = db.Column(db.Float, default=0.0)          # Рейтинг 0-5
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def to_dict(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'period_start': self.period_start.isoformat() if self.period_start else None,
            'period_end': self.period_end.isoformat() if self.period_end else None,
            'tasks_completed': self.tasks_completed,
            'tasks_on_time': self.tasks_on_time,
            'on_time_percentage': (self.tasks_on_time / self.tasks_completed * 100) if self.tasks_completed > 0 else 0,
            'total_hours': self.total_hours,
            'quality_score': self.quality_score,
            'efficiency_score': self.efficiency_score,
            'workload_percentage': self.workload_percentage,
            'rating': self.rating,
            'created_at': self.created_at.isoformat() if self.created_at else None,
        }

class AIRecommendation(db.Model):
    """Рекомендация от ИИ"""
    __tablename__ = 'ai_recommendations'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='CASCADE'), nullable=False)
    task_id = db.Column(db.Integer, db.ForeignKey('tasks.id', ondelete='CASCADE'))
    recommendation_type = db.Column(db.String(50), nullable=False)  # task_assignment, skill_development, workload_adjustment
    title = db.Column(db.String(255), nullable=False)
    description = db.Column(db.Text)
    priority = db.Column(db.String(20), default='medium')  # low, medium, high
    status = db.Column(db.String(20), default='pending')   # pending, accepted, rejected, implemented
    confidence_score = db.Column(db.Float, default=0.0)    # Уверенность ИИ 0-1
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    accepted_at = db.Column(db.DateTime)
    
    def to_dict(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'task_id': self.task_id,
            'recommendation_type': self.recommendation_type,
            'title': self.title,
            'description': self.description,
            'priority': self.priority,
            'status': self.status,
            'confidence_score': self.confidence_score,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'accepted_at': self.accepted_at.isoformat() if self.accepted_at else None,
        }