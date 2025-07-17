from flask import Flask
from flask_cors import CORS
import os
from config import Config
from models import db
from routes import main_bp

def create_app():
    app = Flask(__name__)
    CORS(app)
    
    # Load configuration
    app.config.from_object(Config)
    
    # Initialize database
    db.init_app(app)
    
    # Register blueprints
    app.register_blueprint(main_bp)
    
    return app

def create_tables(app):
    with app.app_context():
        db.create_all()
        print("✓ Tables ensured")

if __name__ == '__main__':
    print("🚀 Starting Flask server...")
    app = create_app()
    create_tables(app)
    app.run(debug=True)
