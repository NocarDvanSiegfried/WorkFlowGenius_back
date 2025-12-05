import pickle
import os
import sys
from sklearn.preprocessing import StandardScaler, LabelEncoder
import pandas as pd

class MLService:
    def __init__(self, model_path=None):
        self.model = None
        self.scaler = StandardScaler()
        self.label_encoders = {}
        self.is_loaded = False
        
        # Определяем путь к модели
        if model_path is None:
            # Ищем модель в разных местах
            possible_paths = [
                os.path.join('ml', 'xgboost_model.pkl'),
                os.path.join('ml', 'xgboost_model_ver2.pkl'),
                os.path.join(os.path.dirname(__file__), '..', 'ml', 'xgboost_model.pkl'),
                'xgboost_model.pkl'
            ]
            
            for path in possible_paths:
                if os.path.exists(path):
                    model_path = path
                    break
        
        self.model_path = model_path
        self.load_model()
    
    def load_model(self):
        """Загрузить ML модель и связанные объекты"""
        try:
            if self.model_path and os.path.exists(self.model_path):
                with open(self.model_path, 'rb') as file:
                    self.model = pickle.load(file)
                print(f"✅ ML модель загружена из: {self.model_path}")
            else:
                print(f"⚠️ Модель не найдена по пути: {self.model_path}")
                print("   Работаем в режиме эмуляции")
                return False
            
            # Инициализация энкодеров
            self._initialize_encoders()
            
            # Инициализация скейлера
            self._initialize_scaler()
            
            self.is_loaded = True
            return True
            
        except Exception as e:
            print(f"❌ Ошибка загрузки модели: {e}")
            print("   Работаем в режиме эмуляции")
            return False
    
    def _initialize_encoders(self):
        """Инициализировать LabelEncoders"""
        # Инициализируем с типичными значениями
        self.label_encoders['skills'] = LabelEncoder()
        self.label_encoders['skills'].fit(['Python', 'JavaScript', 'React', 'SQL', 'Node.js'])
        
        self.label_encoders['task_description'] = LabelEncoder()
        self.label_encoders['task_description'].fit([
            'Interface Development', 
            'Bug Fixing', 
            'API Development', 
            'Database Optimization'
        ])
        
        self.label_encoders['complexity'] = LabelEncoder()
        self.label_encoders['complexity'].fit(['Low', 'Medium', 'High', 'Critical', 'Extreme'])
        
        self.label_encoders['task_priority'] = LabelEncoder()
        self.label_encoders['task_priority'].fit(['Low', 'Medium', 'High', 'Urgent', 'Critical'])
    
    def _initialize_scaler(self):
        """Инициализировать скейлер с демо-данными"""
        # Создаем демо-данные для инициализации скейлера
        import numpy as np
        np.random.seed(42)
        
        demo_data = pd.DataFrame({
            'Satisfaction': np.random.uniform(0, 10, 100),
            'Evaluation': np.random.uniform(0, 10, 100),
            'number_of_projects': np.random.randint(1, 10, 100),
            'average_montly_hours': np.random.randint(120, 200, 100),
            'Salary_INR': np.random.randint(500000, 1500000, 100),
            'Skills': np.random.choice([0, 1, 2, 3, 4], 100),
            'TaskDescription': np.random.choice([0, 1, 2, 3], 100),
            'Complexity': np.random.choice([0, 1, 2, 3, 4], 100),
            'TaskPriority': np.random.choice([0, 1, 2, 3, 4], 100)
        })
        
        self.scaler.fit(demo_data)
    
    def predict_suitability(self, employee_data, task_data):
        """Предсказать совместимость сотрудника и задачи"""
        if not self.is_loaded:
            return self._predict_stub(employee_data, task_data)
        
        try:
            # Подготовка данных для модели
            test_data = pd.DataFrame([{
                'Satisfaction': employee_data.get('satisfaction', 7),
                'Evaluation': employee_data.get('evaluation', 7),
                'number_of_projects': employee_data.get('projects_count', 5),
                'average_montly_hours': employee_data.get('monthly_hours', 160),
                'Salary_INR': employee_data.get('salary', 500) * 1000,  # Конвертация
                'Skills': employee_data.get('skills', 'Python'),
                'TaskDescription': task_data.get('description', 'API Development'),
                'Complexity': task_data.get('complexity', 'Medium'),
                'TaskPriority': task_data.get('priority', 'Medium')
            }])
            
            # Преобразование категориальных признаков
            for col, encoder in self.label_encoders.items():
                if col in test_data.columns:
                    try:
                        test_data[col] = encoder.transform(test_data[col])
                    except ValueError:
                        # Если значения нет в энкодере, используем первое значение
                        test_data[col] = encoder.transform([encoder.classes_[0]])[0]
            
            # Нормализация
            features = test_data.values
            features_normalized = self.scaler.transform(features)
            
            # Предсказание
            prediction = self.model.predict(features_normalized)
            
            return float(prediction[0])
            
        except Exception as e:
            print(f"Ошибка предсказания: {e}")
            return self._predict_stub(employee_data, task_data)
    
    def _predict_stub(self, employee_data, task_data):
        """Заглушка для предсказания когда модель не загружена"""
        import random
        
        score = 0.5
        score += (employee_data.get('efficiency', 7) - 5) * 0.05
        score += (employee_data.get('satisfaction', 7) - 5) * 0.03
        score += random.uniform(-0.1, 0.1)
        
        return max(0.3, min(0.95, score))
    
    def generate_task_recommendations_ml(self, employees, tasks):
        """Сгенерировать рекомендации по задачам с использованием ML"""
        recommendations = []
        
        for task in tasks:
            if task.status != 'pending':
                continue
                
            for employee in employees:
                if employee.role != 'employee':
                    continue
                
                # Проверка загруженности
                workload_ratio = employee.current_workload / employee.max_workload if employee.max_workload > 0 else 0
                if workload_ratio > 0.8:
                    continue
                
                # Подготовка данных
                employee_data = {
                    'satisfaction': employee.satisfaction_score,
                    'evaluation': employee.efficiency_score,
                    'projects_count': employee.current_workload // 10 + 1,
                    'monthly_hours': employee.monthly_hours,
                    'salary': employee.salary,
                    'skills': employee.skills[0].skill_name if employee.skills else 'Python',
                    'efficiency': employee.efficiency_score
                }
                
                task_data = {
                    'description': task.title[:50],
                    'complexity': self._estimate_complexity(task),
                    'priority': task.priority
                }
                
                # Предсказание
                suitability = self.predict_suitability(employee_data, task_data)
                
                if suitability > 0.65:
                    recommendations.append({
                        'user_id': employee.id,
                        'task_id': task.id,
                        'title': f'AI рекомендация: {task.title[:30]}...',
                        'description': f'ИИ рекомендует {employee.name} для задачи "{task.title}". Совместимость: {suitability:.0%}.',
                        'priority': task.priority,
                        'confidence': suitability,
                        'suitability_score': suitability
                    })
        
        return recommendations
    
    def _estimate_complexity(self, task):
        """Оценить сложность задачи на основе её данных"""
        if task.estimated_hours:
            if task.estimated_hours > 20:
                return 'Extreme'
            elif task.estimated_hours > 10:
                return 'Critical'
            elif task.estimated_hours > 5:
                return 'High'
            else:
                return 'Medium'
        elif task.priority == 'urgent':
            return 'High'
        else:
            return 'Medium'

# Создаем глобальный экземпляр
ml_service = MLService()