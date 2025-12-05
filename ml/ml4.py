import pandas as pd
import numpy as np
from sklearn.preprocessing import LabelEncoder, StandardScaler
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_squared_error, r2_score
import xgboost as xgb
import matplotlib.pyplot as plt
import seaborn as sns

# Устанавливаем генератор случайных чисел для воспроизводимости
np.random.seed(42)

# Генерация данных с нормальным распределением

# Для признаков, которые подчиняются нормальному распределению
num_samples = 1000
# Генерация данных с нормальным распределением для разных признаков
satisfaction = np.random.normal(7, 1.5, num_samples)  # Среднее = 7, Стандартное отклонение = 1.5
evaluation = np.random.normal(7, 1, num_samples)      # Среднее = 7, Стандартное отклонение = 1

# Взаимозависимость между количеством проектов и удовлетворенностью
number_of_projects = np.random.normal(5, 2, num_samples).astype(int)
satisfaction -= np.clip(number_of_projects * 0.3, 0, 3)  # Снижение удовлетворенности с увеличением числа проектов

# Генерация зарплаты с зависимостью от количества проектов
salary_inr = np.random.normal(800000, 250000, num_samples).astype(int) + number_of_projects * 20000

# Применяем ограничения на количество проектов и зарплату, чтобы избежать отрицательных значений
number_of_projects = np.clip(number_of_projects, 1, 10)
salary_inr = np.clip(salary_inr, 500000, 1500000)

# Навыки сотрудников
skills = ['Python', 'JavaScript', 'React', 'SQL', 'Node.js']
skills_data = np.random.choice(skills, num_samples)

# Задачи
task_description = np.random.choice(['Interface Development', 'Bug Fixing', 'API Development', 'Database Optimization'], num_samples)
complexity = np.random.choice(['Low', 'Medium', 'High', 'Critical', 'Extreme'], num_samples)
task_priority = np.random.choice(['Low', 'Medium', 'High', 'Urgent', 'Critical'], num_samples)

# Зависимость между навыками и сложностью задач
task_complexity_mapping = {
    'Python': ['High', 'Critical', 'Extreme'],
    'JavaScript': ['Low', 'Medium'],
    'React': ['Medium', 'High'],
    'SQL': ['Medium', 'Critical'],
    'Node.js': ['Low', 'High', 'Critical']
}

# Применяем зависимость для назначения задач
task_complexity = []
for skill in skills_data:
    task_complexity.append(np.random.choice(task_complexity_mapping[skill]))

# Создаем DataFrame для сотрудников
employee_data = pd.DataFrame({
    'EmployeeID': range(1, num_samples + 1),
    'Satisfaction': satisfaction,
    'Evaluation': evaluation,
    'number_of_projects': number_of_projects,
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
    'Complexity': task_complexity,
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

# 2. Зависимость между количеством проектов и удовлетворенностью (до нормализации)
plt.figure(figsize=(10, 6))
sns.scatterplot(x=employee_task_data['number_of_projects'], y=employee_task_data['Satisfaction'], color='purple')
plt.title('Зависимость между количеством проектов и удовлетворенностью')
plt.xlabel('Количество проектов')
plt.ylabel('Удовлетворенность')
plt.show()

# 3. Зависимость между зарплатой и количеством проектов (до нормализации)
plt.figure(figsize=(10, 6))
sns.scatterplot(x=employee_task_data['number_of_projects'], y=employee_task_data['Salary_INR'], color='green')
plt.title('Зависимость между зарплатой и количеством проектов')
plt.xlabel('Количество проектов')
plt.ylabel('Зарплата (INR)')
plt.show()

plt.figure(figsize=(10, 6))
sns.boxplot(x=employee_task_data['number_of_projects'], y=employee_task_data['Satisfaction'], color='purple')
plt.title('Зависимость между количеством проектов и удовлетворенностью')
plt.xlabel('Количество проектов')
plt.ylabel('Удовлетворенность')
plt.show()

# Зависимость между зарплатой и количеством проектов (ящик с усами)
plt.figure(figsize=(10, 6))
sns.boxplot(x=employee_task_data['number_of_projects'], y=employee_task_data['Salary_INR'], color='green')
plt.title('Зависимость между зарплатой и количеством проектов')
plt.xlabel('Количество проектов')
plt.ylabel('Зарплата (INR)')
plt.show()

# Нормализуем числовые признаки
scaler = StandardScaler()
features_to_normalize = ['Satisfaction', 'Evaluation', 'number_of_projects', 'Salary_INR', 'Skills', 'Complexity', 'TaskPriority', 'TaskDescription']
employee_task_data[features_to_normalize] = scaler.fit_transform(employee_task_data[features_to_normalize])

# Генерация целевой переменной (SuitabilityScore) с зависимостями
employee_task_data['SuitabilityScore'] = (
    employee_task_data['Evaluation'] * 0.4 +  # Увеличенный вес для оценки
    employee_task_data['Satisfaction'] * 0.3 +  # Увеличенный вес для удовлетворенности
    employee_task_data['number_of_projects'] * 0.3 + 
    employee_task_data['Salary_INR'] * 0.2 +  # Увеличение веса зарплаты
    employee_task_data['Complexity'] * 0.15 +  # Влияние сложности
    employee_task_data['TaskPriority'] * 0.1 +
    np.random.normal(0, 0.1, len(employee_task_data))  # Добавляем нормальный шум
)

# Применяем Sigmoid для масштабирования SuitabilityScore в диапазон [0, 1]
employee_task_data['SuitabilityScore'] = 1 / (1 + np.exp(-employee_task_data['SuitabilityScore']))

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
import pickle
with open('xgboost_model_ver2.pkl', 'wb') as file:
    pickle.dump(model, file)

# Сотрудники и задачи для тестирования
test_employees = pd.DataFrame({
    'EmployeeID': [1001, 1002, 1003],
    'Satisfaction': [8, 6, 9],
    'Evaluation': [7, 5, 8],
    'number_of_projects': [4, 6, 2],
    'Salary_INR': [950000, 700000, 1200000],
    'Skills': ['Python', 'JavaScript', 'SQL']
})

# Задачи для тестирования
tasks = pd.DataFrame({
    'TaskID': [2001, 2002, 2003],
    'TaskDescription': ['API Development', 'Bug Fixing', 'Database Optimization'],
    'Complexity': ['Medium', 'Low', 'High'],
    'TaskPriority': ['High', 'Medium', 'Urgent']
})

# Применяем Label Encoding для 'Skills'
test_employees['Skills'] = label_encoder_skills.transform(test_employees['Skills'])

# Применяем Label Encoding к задачам
label_encoder_task_desc = LabelEncoder()
tasks['TaskDescription'] = label_encoder_task_desc.fit_transform(tasks['TaskDescription'])

label_encoder_complexity = LabelEncoder()
tasks['Complexity'] = label_encoder_complexity.fit_transform(tasks['Complexity'])

label_encoder_task_priority = LabelEncoder()
tasks['TaskPriority'] = label_encoder_task_priority.fit_transform(tasks['TaskPriority'])

# Объединяем данные сотрудников и задачи (используем cross join)
test_employee_task_data = pd.merge(test_employees, tasks, how='cross')

# Нормализуем числовые признаки
test_employee_task_data[features_to_normalize] = scaler.transform(test_employee_task_data[features_to_normalize])

# Прогнозируем пригодность (SuitabilityScore)
# Удаляем лишние столбцы, такие как 'SuitabilityScore', 'EmployeeID' и 'TaskID'
test_predictions = model.predict(test_employee_task_data.drop(columns=['EmployeeID', 'TaskID']))

# Добавляем предсказанные значения в DataFrame
test_employee_task_data['Predicted_SuitabilityScore'] = test_predictions

# Печатаем результаты для каждого сотрудника и задачи
for i, row in test_employee_task_data.iterrows():
    print(f"Сотрудник {row['EmployeeID']} с задачей '{row['TaskID']}':")
    print(f"Предсказанная пригодность: {row['Predicted_SuitabilityScore']:.4f}")
    print("--------")
import matplotlib.pyplot as plt
import seaborn as sns

plt.figure(figsize=(10, 6))
sns.histplot(employee_task_data['SuitabilityScore'], kde=True, color='blue')
plt.title('Распределение целевой переменной (SuitabilityScore)')
plt.xlabel('SuitabilityScore')
plt.ylabel('Частота')
plt.show()
