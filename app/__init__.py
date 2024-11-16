from flask import Flask
from app.routes.project import bp as project_bp

def create_app():
    """Cria e configura a aplicação Flask."""
    app = Flask(__name__)

    # Registra Blueprints
    app.register_blueprint(project_bp)

    return app
