"""
Database configuration for OCR A-Level Computer Science AI Tutor
"""
import os
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate

# Create SQLAlchemy instance
db = SQLAlchemy()
migrate = Migrate()

class DatabaseConfig:
    """Database configuration class"""
    
    def __init__(self, app=None):
        """Initialize database configuration"""
        self.app = app
        
        if app is not None:
            self.init_app(app)
    
    def init_app(self, app):
        """Initialize database with Flask app"""
        self.app = app
        
        # Configure SQLAlchemy
        app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URI', 'sqlite:///app.db')
        app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = os.environ.get('SQLALCHEMY_TRACK_MODIFICATIONS', 'False').lower() == 'true'
        app.config['SQLALCHEMY_ECHO'] = os.environ.get('SQLALCHEMY_ECHO', 'False').lower() == 'true'
        
        # Initialize SQLAlchemy and Migrate
        db.init_app(app)
        migrate.init_app(app, db)
        
        # Add database to Flask app context
        app.extensions['database'] = self
        
        return self
    
    def create_all(self):
        """Create all database tables"""
        with self.app.app_context():
            db.create_all()
    
    def drop_all(self):
        """Drop all database tables"""
        with self.app.app_context():
            db.drop_all()
    
    def reset_db(self):
        """Reset database (drop and recreate all tables)"""
        with self.app.app_context():
            db.drop_all()
            db.create_all()

# Create database configuration instance
database = DatabaseConfig()
