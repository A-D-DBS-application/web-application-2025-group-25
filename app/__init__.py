from flask import Flask
import os
from app.config import Config
from app import routes
from app.models import db


def create_app(config_class=Config):
    """Application factory function"""
    # Get the root directory (parent of app directory)
    root_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    template_dir = os.path.join(root_dir, 'templates')
    static_dir = os.path.join(root_dir, 'static')
    
    app = Flask(__name__, 
                template_folder=template_dir,
                static_folder=static_dir)
    
    # Load configuration
    app.config.from_object(config_class)
    
    # Initialize database
    db.init_app(app)
    
    # Create tables if they don't exist
    # Note: This will create tables according to the models, but may not match exact ERD schema
    # For production, create tables manually via Supabase SQL Editor
    with app.app_context():
        try:
            # Test connection first
            db.engine.connect()
            print("✓ Database connection successful")
            
            # Create tables if they don't exist
            print("📋 Creating database tables if they don't exist...")
            db.create_all()
            print("✓ Database tables ready")
        except Exception as e:
            print(f"⚠ Warning: Could not connect to database: {e}")
            print("⚠ The app will continue but database operations will fail.")
            print("⚠ Please check your Supabase connection settings.")
    
    # Register blueprint for routes
    app.register_blueprint(routes.bp)
    
    # Register template filter for currency formatting
    @app.template_filter('currency')
    def currency_filter(value):
        """Jinja2 filter for currency formatting with thousand separators"""
        try:
            num = int(round(float(value)))
            # Format with thousand separators (using dot for thousands in European format)
            return f"{num:,}".replace(',', '.')
        except (ValueError, TypeError):
            return str(value)
    
    return app

