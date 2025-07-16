from flask import Flask, jsonify
from flask_cors import CORS
from config import config
from backend.models1 import db, ColumnMapping
from routes.fbdi_routes import fbdi_bp
from routes.ucm_routes import ucm_bp
import os

def create_app(config_name='development'):
    app = Flask(__name__)
    
    # Load configuration
    app.config.from_object(config[config_name])
    
    # Initialize CORS
    CORS(app)
    
    # Ensure instance directory exists
    instance_path = os.path.join(os.path.dirname(__file__), 'instance')
    os.makedirs(instance_path, exist_ok=True)
    
    # Initialize database
    db.init_app(app)
    
    # Register blueprints
    app.register_blueprint(fbdi_bp)
    app.register_blueprint(ucm_bp)
    
    # Health check endpoint
    @app.route('/health')
    def health_check():
        return jsonify({"status": "healthy", "service": "FBDI Generator"})
    
    # Database test endpoint
    @app.route('/test-db')
    def test_db():
        try:
            count = ColumnMapping.query.count()
            return jsonify({"status": "ok", "mapping_count": count})
        except Exception as e:
            return jsonify({"error": str(e)}), 500
    
    return app

def create_tables(app):
    """Create database tables"""
    with app.app_context():
        db.create_all()
        print("✓ Database tables ensured")

if __name__ == '__main__':
    app = create_app()
    print("🚀 Starting Flask server with Oracle Fusion UCM integration...")
    create_tables(app)
    app.run(debug=True)
