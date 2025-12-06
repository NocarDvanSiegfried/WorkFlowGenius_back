"""
Скрипт для заполнения базы данных тестовыми данными
Запуск: python seed_db.py
"""
from app import create_app
from app.database import db
from app.models import (
    User, Task, Assignment, UserCompetency, WorkPreference,
    TeamConnection, AISettings, ModelMetrics, TaskTag, TaskComment, TimeTracking
)
from datetime import datetime, timedelta
from werkzeug.security import generate_password_hash
import random

def seed_database():
    """Заполнить базу данных тестовыми данными"""
    app = create_app()
    
    with app.app_context():
        # Очистка базы данных
        print("Очистка базы данных...")
        db.drop_all()
        db.create_all()
        
        # Создание менеджеров
        print("Создание менеджеров...")
        managers = []
        manager_data = [
            {'name': 'Иван Петров', 'email': 'manager1@example.com'},
            {'name': 'Мария Сидорова', 'email': 'manager2@example.com'},
        ]
        for data in manager_data:
            manager = User(
                email=data['email'],
                name=data['name'],
                password_hash=generate_password_hash('password123'),
                role='manager',
                current_workload=0,
                max_workload=100,
                satisfaction=9,
                efficiency=95,
                avg_hours_per_month=180,
                salary='150000'
            )
            db.session.add(manager)
            managers.append(manager)
        db.session.commit()
        
        # Создание сотрудников
        print("Создание сотрудников...")
        employees = []
        employee_data = [
            {'name': 'Алексей Иванов', 'email': 'alex@example.com', 'skills': ['Python', 'Django', 'PostgreSQL'], 'workload': 60, 'efficiency': 90},
            {'name': 'Елена Смирнова', 'email': 'elena@example.com', 'skills': ['JavaScript', 'React', 'Node.js'], 'workload': 45, 'efficiency': 95},
            {'name': 'Дмитрий Козлов', 'email': 'dmitry@example.com', 'skills': ['Python', 'Flask', 'SQL'], 'workload': 70, 'efficiency': 85},
            {'name': 'Анна Волкова', 'email': 'anna@example.com', 'skills': ['TypeScript', 'Vue.js', 'CSS'], 'workload': 50, 'efficiency': 92},
            {'name': 'Сергей Новиков', 'email': 'sergey@example.com', 'skills': ['Java', 'Spring', 'MySQL'], 'workload': 55, 'efficiency': 88},
            {'name': 'Ольга Морозова', 'email': 'olga@example.com', 'skills': ['Python', 'FastAPI', 'MongoDB'], 'workload': 65, 'efficiency': 90},
        ]
        
        for data in employee_data:
            employee = User(
                email=data['email'],
                name=data['name'],
                password_hash=generate_password_hash('password123'),
                role='employee',
                current_workload=data['workload'],
                max_workload=100,
                satisfaction=random.randint(7, 10),
                efficiency=data['efficiency'],
                avg_hours_per_month=random.randint(150, 180),
                salary=str(random.randint(80000, 120000))
            )
            db.session.add(employee)
            db.session.flush()
            
            # Добавляем компетенции
            for skill in data['skills']:
                competency = UserCompetency(
                    user_id=employee.id,
                    skill_name=skill,
                    level=random.randint(3, 5)
                )
                db.session.add(competency)
            
            # Добавляем предпочтения времени работы
            preference = WorkPreference(
                user_id=employee.id,
                preferred_start_time='09:00',
                preferred_end_time='18:00',
                preferred_days='monday,tuesday,wednesday,thursday,friday'
            )
            db.session.add(preference)
            
            employees.append(employee)
        
        db.session.commit()
        
        # Создание задач
        print("Создание задач...")
        tasks = []
        task_templates = [
            {'title': 'Разработать API для аутентификации', 'description': 'Создать REST API для регистрации и входа пользователей', 'priority': 'high', 'skills': ['Python', 'Flask']},
            {'title': 'Создать компонент формы входа', 'description': 'Разработать React компонент для формы авторизации', 'priority': 'medium', 'skills': ['JavaScript', 'React']},
            {'title': 'Оптимизировать запросы к БД', 'description': 'Улучшить производительность SQL запросов', 'priority': 'high', 'skills': ['SQL', 'PostgreSQL']},
            {'title': 'Написать тесты для API', 'description': 'Создать unit и integration тесты', 'priority': 'medium', 'skills': ['Python', 'Django']},
            {'title': 'Реализовать пагинацию', 'description': 'Добавить пагинацию для списка задач', 'priority': 'low', 'skills': ['JavaScript', 'React']},
            {'title': 'Настроить CI/CD', 'description': 'Настроить автоматическую сборку и деплой', 'priority': 'high', 'skills': ['Python', 'Django']},
            {'title': 'Создать дашборд аналитики', 'description': 'Разработать страницу с графиками и статистикой', 'priority': 'medium', 'skills': ['TypeScript', 'Vue.js']},
            {'title': 'Исправить баги в форме', 'description': 'Исправить ошибки валидации в форме создания задачи', 'priority': 'urgent', 'skills': ['JavaScript', 'React']},
            {'title': 'Добавить фильтры поиска', 'description': 'Реализовать фильтрацию задач по статусу и приоритету', 'priority': 'medium', 'skills': ['Python', 'Flask']},
            {'title': 'Обновить документацию', 'description': 'Обновить README и добавить примеры использования', 'priority': 'low', 'skills': ['Python', 'Django']},
        ]
        
        statuses = ['pending', 'assigned', 'in_progress', 'review', 'completed']
        
        for i, template in enumerate(task_templates):
            deadline = datetime.utcnow() + timedelta(days=random.randint(1, 30))
            task = Task(
                title=template['title'],
                description=template['description'],
                priority=template['priority'],
                status=statuses[i % len(statuses)],
                deadline=deadline,
                estimated_hours=random.randint(4, 40),
                required_competencies=template['skills'],
                created_by=managers[0].id,
                rating=random.randint(3, 5) if statuses[i % len(statuses)] == 'completed' else None
            )
            db.session.add(task)
            db.session.flush()
            
            # Назначаем задачи сотрудникам
            if task.status != 'pending':
                # Выбираем подходящего сотрудника по навыкам
                suitable_employees = [e for e in employees if any(skill in [c.skill_name for c in e.competencies] for skill in template['skills'])]
                if not suitable_employees:
                    suitable_employees = employees
                
                assigned_employee = random.choice(suitable_employees)
                assignment = Assignment(
                    task_id=task.id,
                    assigned_to=assigned_employee.id,
                    assigned_by=managers[0].id,
                    status=task.status,
                    workload_points=random.randint(10, 30),
                    suitability_score=random.uniform(0.7, 1.0)
                )
                db.session.add(assignment)
                
                # Добавляем теги
                tags = ['важно', 'срочно', 'разработка', 'тестирование']
                for tag_name in random.sample(tags, random.randint(1, 2)):
                    tag = TaskTag(
                        task_id=task.id,
                        tag_name=tag_name
                    )
                    db.session.add(tag)
                
                # Добавляем комментарии
                if random.random() > 0.5:
                    comment = TaskComment(
                        task_id=task.id,
                        user_id=assigned_employee.id,
                        content='Начал работу над задачей'
                    )
                    db.session.add(comment)
                
                # Добавляем время работы
                if task.status in ['in_progress', 'review', 'completed']:
                    time_entry = TimeTracking(
                        task_id=task.id,
                        user_id=assigned_employee.id,
                        start_time=datetime.utcnow() - timedelta(hours=random.randint(1, 8)),
                        end_time=datetime.utcnow() - timedelta(minutes=random.randint(0, 60)) if task.status == 'completed' else None,
                        duration_minutes=random.randint(60, 480)
                    )
                    db.session.add(time_entry)
            
            tasks.append(task)
        
        db.session.commit()
        
        # Создание связей между сотрудниками (Team DNA)
        print("Создание связей между сотрудниками...")
        for i, emp1 in enumerate(employees):
            for emp2 in employees[i+1:]:
                if random.random() > 0.3:  # 70% вероятность связи
                    connection = TeamConnection(
                        user1_id=emp1.id,
                        user2_id=emp2.id,
                        connection_strength=random.uniform(0.5, 1.0),
                        connection_type=random.choice(['strong', 'normal', 'weak']),
                        projects_together=random.randint(1, 5),
                        tasks_together=random.randint(5, 20),
                        synergy_score=random.uniform(0.6, 1.0)
                    )
                    db.session.add(connection)
        
        db.session.commit()
        
        # Создание настроек ИИ
        print("Создание настроек ИИ...")
        ai_settings = AISettings(
            competence_weight=85,
            load_weight=90,
            time_preference_weight=70,
            priority_weight=95,
            auto_balance_enabled=True,
            predict_completion_enabled=True,
            smart_recommendations_enabled=True,
            continuous_learning_enabled=True,
            anonymization_enabled=True,
            model_update_frequency='daily'
        )
        db.session.add(ai_settings)
        
        # Создание метрик модели
        model_metrics = ModelMetrics(
            training_examples=12847,
            accuracy=94.2,
            f1_score=0.91,
            training_time_minutes=8.0
        )
        db.session.add(model_metrics)
        
        db.session.commit()
        
        print(f"\nБаза данных успешно заполнена!")
        print(f"   - Менеджеров: {len(managers)}")
        print(f"   - Сотрудников: {len(employees)}")
        print(f"   - Задач: {len(tasks)}")
        print(f"   - Связей между сотрудниками: {TeamConnection.query.count()}")

if __name__ == '__main__':
    seed_database()

