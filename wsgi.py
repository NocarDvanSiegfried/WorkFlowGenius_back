"""
WSGI entry point for Gunicorn
"""
from app import create_app

# Create application instance for Gunicorn
app = create_app()

if __name__ == "__main__":
    app.run()

