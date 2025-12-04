import pandas as pd
import numpy as np
from sklearn.preprocessing import LabelEncoder, StandardScaler
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_squared_error, r2_score
import xgboost as xgb
import matplotlib.pyplot as plt
import seaborn as sns
import pickle

# Устанавливаем генератор случайных чисел для воспроизводимости
np.random.seed(42)

# Генерация данных
num_samples = 1000
satisfaction = np.random.uniform(0, 10, num_samples)
evaluation = np.random.uniform(0, 10, num_samples)
number_of_projects = np.random.randint(1, 10, num_samples)
average_montly_hours = np.random.randint(120, 200, num_samples)
salary_inr = np.random.randint(500000, 1500000, num_samples)

# Навыки сотрудников
skills = ['Python', 'JavaScript', 'React', 'SQL', 'Node.js']
skills_data = np.random.choice(skills, num_samples)

# Задачи
task_description = np.random.choice(['Interface Development', 'Bug Fixing', 'API Development', 'Database Optimization'], num_samples)
complexity = np.random.choice(['Low', 'Medium', 'High', 'Critical', 'Extreme'], num_samples)
task_priority = np.random.choice(['Low', 'Medium', 'High', 'Urgent', 'Critical'], num_samples)

# Создаем DataFrame для сотрудников
employee_data = pd.DataFrame({
    'EmployeeID': range(1, num_samples + 1),
    'Satisfaction': satisfaction,
    'Evaluation': evaluation,
    'number_of_projects': number_of_projects,
    'average_montly_hours': average_montly_hours,
    'Salary_INR': salary_inr,
    'Skills': skills_data
})

# Применяем Label Encoding к столбцу 'Skills'
label_encoder_skills = LabelEncoder()
employee_data['Skills'] = label_encoder_skills.fit_transform(employee_data['Skills'])

# Генерация данных для задач
task_data = pd.DataFrame({
    'TaskID': range(1, num_samples + 1),
    'TaskDescription': task_description,
    'Complexity': complexity,
    'TaskPriority': task_priority
})

# Применяем Label Encoding к столбцам 'TaskDescription', 'Complexity', 'TaskPriority'
label_encoder_task_desc = LabelEncoder()
task_data['TaskDescription'] = label_encoder_task_desc.fit_transform(task_data['TaskDescription'])

label_encoder_complexity = LabelEncoder()
task_data['Complexity'] = label_encoder_complexity.fit_transform(task_data['Complexity'])

label_encoder_task_priority = LabelEncoder()
task_data['TaskPriority'] = label_encoder_task_priority.fit_transform(task_data['TaskPriority'])

# Объединяем данные сотрудников и задачи (используем cross join)
employee_task_data = pd.merge(employee_data, task_data, how='cross')

# Нормализуем числовые признаки
scaler = StandardScaler()
features_to_normalize = ['Satisfaction', 'Evaluation', 'number_of_projects', 'average_montly_hours', 
                         'Salary_INR', 'Skills', 'Complexity', 'TaskPriority', 'TaskDescription']
employee_task_data[features_to_normalize] = scaler.fit_transform(employee_task_data[features_to_normalize])

# Генерация целевой переменной (SuitabilityScore)
employee_task_data['SuitabilityScore'] = (
    employee_task_data['Evaluation'] * 0.3 +
    employee_task_data['Satisfaction'] * 0.3 +
    employee_task_data['number_of_projects'] * 0.2 +
    employee_task_data['average_montly_hours'] * 0.1 +
    employee_task_data['Complexity'] * 0.05 +
    employee_task_data['TaskPriority'] * 0.05 +
    np.random.uniform(0, 0.1, len(employee_task_data))  # Добавим небольшой шум
)

# Разделяем данные на признаки и целевую переменную
X = employee_task_data.drop(columns=['SuitabilityScore', 'EmployeeID', 'TaskID'])
y = employee_task_data['SuitabilityScore']

# Разделяем данные на обучающие и тестовые выборки
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

# Инициализация и обучение модели XGBoost
model = xgb.XGBRegressor(n_estimators=100, learning_rate=0.1, max_depth=5, random_state=42)
model.fit(X_train, y_train)

# Прогнозы
y_pred = model.predict(X_test)

# Оценка модели
mse = mean_squared_error(y_test, y_pred)
r2 = r2_score(y_test, y_pred)

# Выводим результаты
print(f"Mean Squared Error (MSE): {mse}")
print(f"R²: {r2}")

# Важность признаков
feature_importances = model.feature_importances_
feature_importance_df = pd.DataFrame({
    'Feature': X.columns,
    'Importance': feature_importances
})
feature_importance_df = feature_importance_df.sort_values(by='Importance', ascending=False)

# Визуализируем важность признаков
plt.figure(figsize=(10, 6))
plt.barh(feature_importance_df['Feature'], feature_importance_df['Importance'])
plt.xlabel('Feature Importance')
plt.title('Feature Importance - XGBoost Model')
plt.show()

# Строим корреляционную матрицу
correlation_matrix = X.corr()

# Визуализируем корреляционную матрицу
plt.figure(figsize=(12, 8))
sns.heatmap(correlation_matrix, annot=True, cmap='coolwarm', fmt='.2f', linewidths=0.5)
plt.title('Correlation Matrix of Features')
plt.show()

# Сохранение модели
with open('xgboost_model.pkl', 'wb') as file:
    pickle.dump(model, file)
