"""
Routes package for OCR A-Level Computer Science AI Tutor
"""

from flask import Blueprint, render_template

# Create blueprints
main_bp = Blueprint('main', __name__)
auth_bp = Blueprint('auth', __name__, url_prefix='/auth')
subscription_bp = Blueprint('subscription', __name__, url_prefix='/subscription')
student_bp = Blueprint('student', __name__, url_prefix='/student')
admin_bp = Blueprint('admin', __name__, url_prefix='/admin')
api_bp = Blueprint('api', __name__, url_prefix='/api')

# Import routes
from routes.auth import *
from routes.subscription import *
from routes.student import *
from routes.admin import *
from routes.api import *

# Main routes
@main_bp.route('/')
def index():
    """Home page"""
    return render_template('index.html')

# Register blueprints
def register_blueprints(app):
    """Register blueprints with app"""
    app.register_blueprint(main_bp)
    app.register_blueprint(auth_bp)
    app.register_blueprint(subscription_bp)
    app.register_blueprint(student_bp)
    app.register_blueprint(admin_bp)
    app.register_blueprint(api_bp)
