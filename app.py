"""
OCR A-Level Computer Science AI Tutor
"""
import os
import logging
from flask import Flask, render_template, request, redirect, url_for, flash, jsonify
from flask_login import LoginManager, current_user
from dotenv import load_dotenv
from werkzeug.middleware.proxy_fix import ProxyFix
from datetime import datetime

# Load environment variables
load_dotenv()

# Create Flask app
app = Flask(__name__)

# Configure app
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'dev-key')
app.config['APPLICATION_ROOT'] = os.environ.get('APPLICATION_ROOT', '/')
app.config['PREFERRED_URL_SCHEME'] = os.environ.get('PREFERRED_URL_SCHEME', 'http')
app.config['SERVER_NAME'] = os.environ.get('SERVER_NAME')

# Configure session security
app.config['SESSION_COOKIE_SECURE'] = os.environ.get('SESSION_COOKIE_SECURE', 'False').lower() == 'true'
app.config['REMEMBER_COOKIE_SECURE'] = os.environ.get('REMEMBER_COOKIE_SECURE', 'False').lower() == 'true'
app.config['SESSION_COOKIE_HTTPONLY'] = os.environ.get('SESSION_COOKIE_HTTPONLY', 'True').lower() == 'true'
app.config['REMEMBER_COOKIE_HTTPONLY'] = os.environ.get('REMEMBER_COOKIE_HTTPONLY', 'True').lower() == 'true'

# Configure logging
log_level = getattr(logging, os.environ.get('LOG_LEVEL', 'INFO').upper())
log_file = os.environ.get('LOG_FILE', 'logs/app.log')

# Create logs directory if it doesn't exist
os.makedirs(os.path.dirname(log_file), exist_ok=True)

logging.basicConfig(
    level=log_level,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(log_file),
        logging.StreamHandler()
    ]
)

# Configure ProxyFix for proper IP handling behind proxies
app.wsgi_app = ProxyFix(app.wsgi_app, x_for=1, x_proto=1, x_host=1, x_port=1, x_prefix=1)

# Initialize database
from config.database_config import database
database.init_app(app)

# Initialize services with error handling
try:
    # Initialize Firebase (if available in this branch)
    from config.firebase_config import firebase
    firebase.init_app(app)
    app.logger.info("Firebase initialized successfully")
except Exception as e:
    app.logger.warning(f"Firebase initialization skipped: {e}")

try:
    # Initialize Stripe
    from config.stripe_config import stripe_config
    stripe_config.init_app(app)
    app.logger.info("Stripe initialized successfully")
except Exception as e:
    app.logger.warning(f"Stripe initialization skipped: {e}")

try:
    # Initialize AWS
    from config.aws_config import aws_config
    aws_config.init_app(app)
    app.logger.info("AWS initialized successfully")
except Exception as e:
    app.logger.warning(f"AWS initialization skipped: {e}")

# Initialize login manager
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'auth.login'
login_manager.login_message_category = 'info'

@login_manager.user_loader
def load_user(user_id):
    from models.user import User
    return User.query.get(int(user_id))

# Register blueprints
from routes import register_blueprints
register_blueprints(app)

# Error handlers
@app.errorhandler(404)
def page_not_found(e):
    return render_template('errors/404.html'), 404

@app.errorhandler(500)
def internal_server_error(e):
    app.logger.error(f"Internal server error: {e}")
    return render_template('errors/500.html'), 500

# Context processors
@app.context_processor
def inject_now():
    return {'now': datetime.utcnow()}

@app.context_processor
def inject_user_subscription():
    if current_user.is_authenticated:
        try:
            return {
                'has_subscription': current_user.has_active_subscription(),
                'subscription': current_user.subscription
            }
        except Exception as e:
            app.logger.error(f"Error in subscription context processor: {e}")
            return {'has_subscription': False, 'subscription': None}
    return {'has_subscription': False, 'subscription': None}

# Before request handlers
@app.before_request
def check_maintenance_mode():
    maintenance_mode = os.environ.get('MAINTENANCE_MODE', 'False').lower() == 'true'
    if maintenance_mode and request.path != '/maintenance' and not request.path.startswith('/static/'):
        return render_template('errors/maintenance.html'), 503

# Routes
@app.route('/maintenance')
def maintenance():
    return render_template('errors/maintenance.html')

@app.route('/health')
def health_check():
    """Health check endpoint for AWS"""
    return jsonify({'status': 'ok', 'timestamp': datetime.utcnow().isoformat()})

# Initialize app
with app.app_context():
    # Create database tables if they don't exist
    try:
        database.create_all()
        app.logger.info("Database tables created successfully")
    except Exception as e:
        app.logger.error(f"Error creating database tables: {e}")

    # Create required directories
    os.makedirs('logs', exist_ok=True)
    os.makedirs('migrations', exist_ok=True)
    os.makedirs('temp_uploads', exist_ok=True)
    os.makedirs('resources', exist_ok=True)

# Run app
if __name__ == '__main__':
    app.run(debug=os.environ.get('FLASK_ENV', 'production') == 'development')
