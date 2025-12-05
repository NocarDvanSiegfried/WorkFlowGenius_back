from flask import Flask, request, jsonify
import xgboost as xgb
import pickle
import numpy as np
from sklearn.preprocessing import StandardScaler

app = Flask(__name__)

# Загружаем обученную модель
with open('xgboost_model.pkl', 'rb') as file:
    model = pickle.load(file)

# Создаем скейлер (используется тот же, что и при обучении)
scaler = StandardScaler()

# Эндпоинт для получения данных и предсказания
@app.route('/predict', methods=['POST'])
def predict():
    data = request.get_json()  # Получаем данные в формате JSON
    # Данные из запроса (пример)
    # {'Satisfaction': 8, 'Evaluation': 9, 'number_of_projects': 5, 'average_montly_hours': 150, ...}

    # Извлекаем признаки
    features = [
        data['Satisfaction'],
        data['Evaluation'],
        data['number_of_projects'],
        data['average_montly_hours'],
        data['Salary_INR'],
        data['Skills'],
        data['Complexity'],
        data['TaskPriority'],
        data['TaskDescription']
    ]
    
    # Преобразуем данные и нормализуем
    features = np.array(features).reshape(1, -1)
    features_normalized = scaler.transform(features)
    
    # Получаем предсказание
    prediction = model.predict(features_normalized)

    # Возвращаем результат в формате JSON
    return jsonify({'suitability_score': prediction[0]})

if __name__ == '__main__':
    app.run(debug=True)
