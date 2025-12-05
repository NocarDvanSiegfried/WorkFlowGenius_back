from flask import Flask, request, jsonify
import pickle
import numpy as np
from sklearn.preprocessing import StandardScaler
import pandas as pd
from sklearn.preprocessing import LabelEncoder

# Инициализация Flask приложения
app = Flask(__name__)

# Загрузка модели и других объектов
with open('xgboost_model.pkl', 'rb') as file:
    model = pickle.load(file)

# Загрузка скалера
scaler = StandardScaler()

# Загрузка LabelEncoders для обратного преобразования
label_encoder_skills = LabelEncoder()
label_encoder_task_desc = LabelEncoder()
label_encoder_complexity = LabelEncoder()
label_encoder_task_priority = LabelEncoder()

# API для предсказания SuitabilityScore
@app.route('/predict', methods=['POST'])
def predict():
    # Получение данных из запроса
    data = request.get_json()
    # Пример curl запроса
    # curl -X POST -H "Content-Type: application/json" \
    # -d '{"Satisfaction": 8, "Evaluation": 7, "number_of_projects": 4, "Salary_INR": 950000, "Skills": "Python", "TaskDescription": "API Development", "Complexity": "Medium", "TaskPriority": "High"}' \
    # http://127.0.0.1:5000/predict
    # Пример входных данных
    # {
    #     "Satisfaction": 8,
    #     "Evaluation": 7,
    #     "number_of_projects": 4,
    #     "Salary_INR": 950000,
    #     "Skills": "Python",
    #     "TaskDescription": "API Development",
    #     "Complexity": "Medium",
    #     "TaskPriority": "High"
    # }

    # Преобразование входных данных в DataFrame
    test_data = pd.DataFrame([data])

    # Применяем LabelEncoding и нормализацию
    test_data['Skills'] = label_encoder_skills.transform(test_data['Skills'])
    test_data['TaskDescription'] = label_encoder_task_desc.transform(test_data['TaskDescription'])
    test_data['Complexity'] = label_encoder_complexity.transform(test_data['Complexity'])
    test_data['TaskPriority'] = label_encoder_task_priority.transform(test_data['TaskPriority'])

    # Нормализуем числовые признаки
    features_to_normalize = ['Satisfaction', 'Evaluation', 'number_of_projects', 'Salary_INR', 'Skills', 'Complexity', 'TaskPriority', 'TaskDescription']
    test_data[features_to_normalize] = scaler.transform(test_data[features_to_normalize])

    # Прогнозирование пригодности (SuitabilityScore)
    prediction = model.predict(test_data.drop(columns=['EmployeeID', 'TaskID']))

    # Возвращаем результат в формате JSON
    return jsonify({'predicted_suitability_score': prediction[0]})

# Запуск приложения
if __name__ == '__main__':
    app.run(debug=True)
