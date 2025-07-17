from flask import Flask, jsonify
from flask_cors import CORS
import os
from config import Config
from models import db
from routes import main_bp
from fbdi_operations import fbdi_bp  # Make sure this import is correct

def create_app():
    app = Flask(__name__)
    
    # Configure CORS properly for all routes
    CORS(app, resources={
        r"/*": {
            "origins": ["http://localhost:3000", "http://localhost:5173"],  # Add your frontend URLs
            "methods": ["GET", "POST", "PUT", "DELETE", "OPTIONS"],
            "allow_headers": ["Content-Type", "Authorization"]
        }
    })
    
    # Load configuration
    app.config.from_object(Config)
    
    # Initialize database
    db.init_app(app)
    
    # Register blueprints
    app.register_blueprint(main_bp)
    app.register_blueprint(fbdi_bp, url_prefix='/fbdi')  # Ensure this line is present
    
    # Global error handlers
    @app.errorhandler(404)
    def not_found(error):
        return jsonify({"error": "Not found"}), 404
    
    @app.errorhandler(500)
    def internal_error(error):
        return jsonify({"error": "Internal server error"}), 500
    
    return app

def create_tables(app):
    with app.app_context():
        try:
            db.create_all()
            print("✓ Tables ensured")
        except Exception as e:
            print(f"Error creating tables: {e}")

if __name__ == '__main__':
    print("🚀 Starting Flask server...")
    app = create_app()
    create_tables(app)
    
    # Print all registered routes for debugging
    print("\n📋 Registered Routes:")
    for rule in app.url_map.iter_rules():
        print(f"  {rule.endpoint}: {rule.rule} [{', '.join(rule.methods)}]")
    
    app.run(debug=True, host='0.0.0.0', port=5000)
