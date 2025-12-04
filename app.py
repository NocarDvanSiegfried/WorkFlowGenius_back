"""
Local development entry point
For production, use wsgi.py with Gunicorn
"""
from app import create_app

if __name__ == '__main__':
    app = create_app()
    app.run(
        host='0.0.0.0',
        port=5000,
        debug=app.config['DEBUG']
    )

