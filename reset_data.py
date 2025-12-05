import os
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import create_app
from app.database import db

app = create_app()

with app.app_context():
    print("Удаление старых таблиц...")
    db.drop_all()
    
    print("Создание новых таблиц...")
    db.create_all()
    
    print("✅ База данных успешно пересоздана!")
    print(f"Путь к базе данных: {app.instance_path}/app.db")