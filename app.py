"""
OCR A-Level Computer Science AI Tutor
"""
import os
import sys
import logging
import traceback
import json
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

# Add debug handler for startup issues
handler = logging.FileHandler('/tmp/app_debug.log')
handler.setLevel(logging.DEBUG)
app.logger.addHandler(handler)
app.logger.setLevel(logging.DEBUG)

# Configure ProxyFix for proper IP handling behind proxies
app.wsgi_app = ProxyFix(app.wsgi_app, x_for=1, x_proto=1, x_host=1, x_port=1, x_prefix=1)

# Startup diagnostics
app.logger.info("=== Starting Application ===")
app.logger.info(f"Python version: {sys.version}")
app.logger.info(f"Working directory: {os.getcwd()}")
app.logger.info(f"Environment variables: DATABASE_URI={os.environ.get('DATABASE_URI', 'Not set')}")

# Debug routes - these will help us diagnose issues
@app.route('/debug')
def debug_info():
    """Debug endpoint for AWS deployment troubleshooting"""
    debug_data = {
        'environment': dict(os.environ),
        'config': {k: str(v) for k, v in app.config.items() if not k.startswith('_')},
        'python_version': sys.version,
        'working_directory': os.getcwd(),
        'directory_contents': os.listdir(),
        'user': os.environ.get('USER'),
    }
    
    # Check specific files
    paths_to_check = [
        '/var/app/current/credentials/firebase-service-account.json',
        '/var/log/eb-engine.log',
        '/var/log/eb-activity.log',
        '/var/log/eb-hooks.log',
        '/tmp/app_debug.log'
    ]
    
    file_checks = {}
    for path in paths_to_check:
        file_checks[path] = {
            'exists': os.path.exists(path),
            'size': os.path.getsize(path) if os.path.exists(path) else None,
            'is_file': os.path.isfile(path) if os.path.exists(path) else None
        }
    
    debug_data['file_checks'] = file_checks
    
    # Try to get database connection info
    try:
        from sqlalchemy import create_engine
        from sqlalchemy.exc import SQLAlchemyError
        
        db_uri = os.environ.get('DATABASE_URI', 'sqlite:///app.db')
        debug_data['database'] = {
            'uri': db_uri.replace(':'+'//'+':'+'@', '://user:pass@') if '//' in db_uri and '@' in db_uri else db_uri,
            'connection_test': 'Not tested'
        }
        
        try:
            engine = create_engine(db_uri)
            conn = engine.connect()
            conn.close()
            debug_data['database']['connection_test'] = 'Success'
        except SQLAlchemyError as e:
            debug_data['database']['connection_test'] = f'Failed: {str(e)}'
    except Exception as e:
        debug_data['database_error'] = str(e)
    
    return jsonify(debug_data)

@app.route('/deploy-test')
def deploy_test():
    """Minimal test route to verify deployment success"""
    return jsonify({
        'status': 'success',
        'message': 'Deployment test successful',
        'timestamp': datetime.utcnow().isoformat(),
        'environment': os.environ.get('FLASK_ENV', 'production')
    })

# Initialize components with error handling
components = [
    ('database', 'config.database_config', 'database'),
    ('firebase', 'config.firebase_config', 'firebase'),
    ('stripe', 'config.stripe_config', 'stripe_config'),
    ('aws', 'config.aws_config', 'aws_config')
]

initialized_components = {}

for name, module_path, attr_name in components:
    try:
        app.logger.info(f"Initializing {name}...")
        module = __import__(module_path, fromlist=[attr_name])
        component = getattr(module, attr_name)
        component.init_app(app)
        initialized_components[name] = True
        app.logger.info(f"{name} initialized successfully")
    except Exception as e:
        app.logger.error(f"Error initializing {name}: {e}")
        app.logger.error(traceback.format_exc())
        initialized_components[name] = False

# Initialize login manager only if database is initialized
if initialized_components.get('database', False):
    try:
        app.logger.info("Initializing login manager...")
        login_manager = LoginManager()
        login_manager.init_app(app)
        login_manager.login_view = 'auth.login'
        login_manager.login_message_category = 'info'

        @login_manager.user_loader
        def load_user(user_id):
            try:
                from models.user import User
                return User.query.get(int(user_id))
            except Exception as e:
                app.logger.error(f"Error loading user: {e}")
                return None
                
        app.logger.info("Login manager initialized successfully")
    except Exception as e:
        app.logger.error(f"Error initializing login manager: {e}")
        app.logger.error(traceback.format_exc())

# Register blueprints only if core dependencies are available
if initialized_components.get('database', False):
    try:
        app.logger.info("Registering blueprints...")
        from routes import register_blueprints
        register_blueprints(app)
        app.logger.info("Blueprints registered successfully")
    except Exception as e:
        app.logger.error(f"Error registering blueprints: {e}")
        app.logger.error(traceback.format_exc())

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
    if current_user.is_authenticated and hasattr(current_user, 'has_active_subscription'):
        try:
            return {
                'has_subscription': current_user.has_active_subscription(),
                'subscription': current_user.subscription
            }
        except Exception as e:
            app.logger.error(f"Error in subscription context processor: {e}")
    return {'has_subscription': False, 'subscription': None}

# Before request handlers
@app.before_request
def check_maintenance_mode():
    maintenance_mode = os.environ.get('MAINTENANCE_MODE', 'False').lower() == 'true'
    if maintenance_mode and request.path != '/maintenance' and not request.path.startswith('/static/'):
        return render_template('errors/maintenance.html'), 503

# Routes
@app.route('/')
def index():
    """Home page"""
    try:
        return render_template('index.html')
    except Exception as e:
        app.logger.error(f"Error rendering index page: {e}")
        return jsonify({
            'error': 'Error rendering index page',
            'message': str(e),
            'initialized_components': initialized_components
        }), 500

@app.route('/maintenance')
def maintenance():
    return render_template('errors/maintenance.html')

@app.route('/health')
def health_check():
    """Health check endpoint for AWS"""
    return jsonify({
        'status': 'ok', 
        'timestamp': datetime.utcnow().isoformat(),
        'initialized_components': initialized_components
    })

# Initialize app
with app.app_context():
    # Create required directories
    os.makedirs('logs', exist_ok=True)
    os.makedirs('migrations', exist_ok=True)
    os.makedirs('temp_uploads', exist_ok=True)
    os.makedirs('resources', exist_ok=True)
    
    # Create database tables if database was initialized successfully
    if initialized_components.get('database', False):
        try:
            app.logger.info("Creating database tables...")
            database.create_all()
            app.logger.info("Database tables created successfully")
        except Exception as e:
            app.logger.error(f"Error creating database tables: {e}")
            app.logger.error(traceback.format_exc())

app.logger.info("=== Application Startup Complete ===")

# Run app
if __name__ == '__main__':
    app.run(debug=os.environ.get('FLASK_ENV', 'production') == 'development')
