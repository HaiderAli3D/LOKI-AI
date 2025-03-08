"""
Admin routes for OCR A-Level Computer Science AI Tutor
"""
from flask import render_template, redirect, url_for, request, flash, jsonify, current_app, abort
from flask_login import login_required, current_user
from routes import admin_bp
from models.user import User
from models.subscription import Subscription
from models.resource import Resource
from models.knowledge_base import KnowledgeBase
from services.resource_service import ResourceService
from services.aws_service import AWSService
from config.database_config import db
from werkzeug.utils import secure_filename
import os
import uuid
from datetime import datetime

# Decorator to check if user is admin
def admin_required(f):
    """Decorator to check if user is admin"""
    def decorated_function(*args, **kwargs):
        if not current_user.is_admin():
            abort(403)
        return f(*args, **kwargs)
    decorated_function.__name__ = f.__name__
    return login_required(decorated_function)

@admin_bp.route('/dashboard')
@admin_required
def dashboard():
    """Admin dashboard"""
    # Get user count
    user_count = User.query.count()
    
    # Get active subscription count
    active_subscription_count = Subscription.query.filter(
        Subscription.status == 'active'
    ).count()
    
    # Get resource count
    resource_count = Resource.query.count()
    
    # Get knowledge base entry count
    knowledge_base_count = KnowledgeBase.query.count()
    
    # Get recent users
    recent_users = User.query.order_by(User.created_at.desc()).limit(5).all()
    
    # Get recent subscriptions
    recent_subscriptions = Subscription.query.order_by(Subscription.created_at.desc()).limit(5).all()
    
    # Get recent resources
    recent_resources = Resource.query.order_by(Resource.created_at.desc()).limit(5).all()
    
    return render_template('admin/dashboard.html',
                          user_count=user_count,
                          active_subscription_count=active_subscription_count,
                          resource_count=resource_count,
                          knowledge_base_count=knowledge_base_count,
                          recent_users=recent_users,
                          recent_subscriptions=recent_subscriptions,
                          recent_resources=recent_resources)

@admin_bp.route('/users')
@admin_required
def users():
    """User management page"""
    # Get users
    users = User.query.all()
    
    return render_template('admin/users.html', users=users)

@admin_bp.route('/user/<int:user_id>')
@admin_required
def user(user_id):
    """User details page"""
    # Get user
    user = User.query.get_or_404(user_id)
    
    # Get user's subscription
    subscription = Subscription.query.filter_by(user_id=user_id).first()
    
    # Get user's recent sessions
    recent_sessions = user.get_recent_sessions()
    
    return render_template('admin/user.html',
                          user=user,
                          subscription=subscription,
                          recent_sessions=recent_sessions)

@admin_bp.route('/user/<int:user_id>/edit', methods=['GET', 'POST'])
@admin_required
def edit_user(user_id):
    """Edit user page"""
    # Get user
    user = User.query.get_or_404(user_id)
    
    if request.method == 'POST':
        # Update user
        user.first_name = request.form.get('first_name')
        user.last_name = request.form.get('last_name')
        user.role = request.form.get('role')
        user.is_active = 'is_active' in request.form
        
        db.session.commit()
        
        flash('User updated successfully', 'success')
        return redirect(url_for('admin.user', user_id=user_id))
    
    return render_template('admin/edit_user.html', user=user)

@admin_bp.route('/user/<int:user_id>/delete', methods=['POST'])
@admin_required
def delete_user(user_id):
    """Delete user"""
    # Get user
    user = User.query.get_or_404(user_id)
    
    # Delete user
    db.session.delete(user)
    db.session.commit()
    
    flash('User deleted successfully', 'success')
    return redirect(url_for('admin.users'))

@admin_bp.route('/subscriptions')
@admin_required
def subscriptions():
    """Subscription management page"""
    # Get subscriptions
    subscriptions = Subscription.query.all()
    
    return render_template('admin/subscriptions.html', subscriptions=subscriptions)

@admin_bp.route('/subscription/<int:subscription_id>')
@admin_required
def subscription(subscription_id):
    """Subscription details page"""
    # Get subscription
    subscription = Subscription.query.get_or_404(subscription_id)
    
    # Get user
    user = User.query.get(subscription.user_id)
    
    return render_template('admin/subscription.html',
                          subscription=subscription,
                          user=user)

@admin_bp.route('/resources')
@admin_required
def resources():
    """Resource management page"""
    # Get topic ID from query parameters
    topic_id = request.args.get('topic_id')
    
    # Get resources
    resources = Resource.get_resources(topic_id, is_public=None)
    
    # Get topics
    topics = [
        {'id': 'data_types', 'name': 'Data Types'},
        {'id': 'data_structures', 'name': 'Data Structures'},
        {'id': 'algorithms', 'name': 'Algorithms'},
        {'id': 'programming', 'name': 'Programming'},
        {'id': 'computer_systems', 'name': 'Computer Systems'},
        {'id': 'networking', 'name': 'Networking'},
        {'id': 'databases', 'name': 'Databases'},
        {'id': 'theory_of_computation', 'name': 'Theory of Computation'}
    ]
    
    return render_template('admin/resources.html',
                          resources=resources,
                          topics=topics,
                          selected_topic=topic_id)

@admin_bp.route('/resource/<int:resource_id>')
@admin_required
def resource(resource_id):
    """Resource details page"""
    # Get resource
    resource = Resource.query.get_or_404(resource_id)
    
    # Get knowledge base entries for resource
    knowledge_base_entries = KnowledgeBase.query.filter_by(resource_id=resource_id).all()
    
    # Generate presigned URL if resource has file path
    presigned_url = None
    if resource.file_path:
        presigned_url = AWSService.generate_presigned_url(resource.file_path)
    
    return render_template('admin/resource.html',
                          resource=resource,
                          knowledge_base_entries=knowledge_base_entries,
                          presigned_url=presigned_url)

@admin_bp.route('/resource/<int:resource_id>/edit', methods=['GET', 'POST'])
@admin_required
def edit_resource(resource_id):
    """Edit resource page"""
    # Get resource
    resource = Resource.query.get_or_404(resource_id)
    
    if request.method == 'POST':
        # Update resource
        title = request.form.get('title')
        description = request.form.get('description')
        topic_id = request.form.get('topic_id')
        is_public = 'is_public' in request.form
        
        # Update resource
        ResourceService.update_resource(
            resource_id=resource_id,
            title=title,
            description=description,
            topic_id=topic_id,
            is_public=is_public
        )
        
        flash('Resource updated successfully', 'success')
        return redirect(url_for('admin.resource', resource_id=resource_id))
    
    # Get topics
    topics = [
        {'id': 'data_types', 'name': 'Data Types'},
        {'id': 'data_structures', 'name': 'Data Structures'},
        {'id': 'algorithms', 'name': 'Algorithms'},
        {'id': 'programming', 'name': 'Programming'},
        {'id': 'computer_systems', 'name': 'Computer Systems'},
        {'id': 'networking', 'name': 'Networking'},
        {'id': 'databases', 'name': 'Databases'},
        {'id': 'theory_of_computation', 'name': 'Theory of Computation'}
    ]
    
    return render_template('admin/edit_resource.html',
                          resource=resource,
                          topics=topics)

@admin_bp.route('/resource/<int:resource_id>/delete', methods=['POST'])
@admin_required
def delete_resource(resource_id):
    """Delete resource"""
    # Delete resource
    success = ResourceService.delete_resource(resource_id)
    
    if success:
        flash('Resource deleted successfully', 'success')
    else:
        flash('Error deleting resource', 'danger')
    
    return redirect(url_for('admin.resources'))

@admin_bp.route('/upload', methods=['GET', 'POST'])
@admin_required
def upload():
    """Upload resource page"""
    if request.method == 'POST':
        # Get form data
        title = request.form.get('title')
        description = request.form.get('description')
        topic_id = request.form.get('topic_id')
        is_public = 'is_public' in request.form
        
        # Get file
        file = request.files.get('file')
        
        if not file:
            flash('No file selected', 'danger')
            return redirect(url_for('admin.upload'))
        
        # Check if file is allowed
        if not AWSService.is_allowed_file(file.filename):
            flash('File type not allowed', 'danger')
            return redirect(url_for('admin.upload'))
        
        # Get file type
        file_type = AWSService.get_file_extension(file.filename)[1:]
        
        # Create resource
        resource = ResourceService.create_resource(
            title=title,
            file=file,
            file_type=file_type,
            description=description,
            topic_id=topic_id,
            is_public=is_public,
            created_by=current_user.id
        )
        
        if resource:
            flash('Resource uploaded successfully', 'success')
            return redirect(url_for('admin.resource', resource_id=resource.id))
        else:
            flash('Error uploading resource', 'danger')
            return redirect(url_for('admin.upload'))
    
    # Get topics
    topics = [
        {'id': 'data_types', 'name': 'Data Types'},
        {'id': 'data_structures', 'name': 'Data Structures'},
        {'id': 'algorithms', 'name': 'Algorithms'},
        {'id': 'programming', 'name': 'Programming'},
        {'id': 'computer_systems', 'name': 'Computer Systems'},
        {'id': 'networking', 'name': 'Networking'},
        {'id': 'databases', 'name': 'Databases'},
        {'id': 'theory_of_computation', 'name': 'Theory of Computation'}
    ]
    
    return render_template('admin/upload.html', topics=topics)

@admin_bp.route('/knowledge-base')
@admin_required
def knowledge_base():
    """Knowledge base management page"""
    # Get topic ID from query parameters
    topic_id = request.args.get('topic_id')
    
    # Get knowledge base entries
    if topic_id:
        entries = KnowledgeBase.query.filter_by(topic_id=topic_id).all()
    else:
        entries = KnowledgeBase.query.all()
    
    # Get topics
    topics = [
        {'id': 'data_types', 'name': 'Data Types'},
        {'id': 'data_structures', 'name': 'Data Structures'},
        {'id': 'algorithms', 'name': 'Algorithms'},
        {'id': 'programming', 'name': 'Programming'},
        {'id': 'computer_systems', 'name': 'Computer Systems'},
        {'id': 'networking', 'name': 'Networking'},
        {'id': 'databases', 'name': 'Databases'},
        {'id': 'theory_of_computation', 'name': 'Theory of Computation'}
    ]
    
    return render_template('admin/knowledge_base.html',
                          entries=entries,
                          topics=topics,
                          selected_topic=topic_id)

@admin_bp.route('/knowledge-base/create', methods=['GET', 'POST'])
@admin_required
def create_knowledge_base_entry():
    """Create knowledge base entry page"""
    if request.method == 'POST':
        # Get form data
        topic_id = request.form.get('topic_id')
        title = request.form.get('title')
        content = request.form.get('content')
        source = request.form.get('source')
        
        # Create knowledge base entry
        entry = KnowledgeBase(
            topic_id=topic_id,
            title=title,
            content=content,
            source=source,
            created_by=current_user.id
        )
        
        db.session.add(entry)
        db.session.commit()
        
        flash('Knowledge base entry created successfully', 'success')
        return redirect(url_for('admin.knowledge_base'))
    
    # Get topics
    topics = [
        {'id': 'data_types', 'name': 'Data Types'},
        {'id': 'data_structures', 'name': 'Data Structures'},
        {'id': 'algorithms', 'name': 'Algorithms'},
        {'id': 'programming', 'name': 'Programming'},
        {'id': 'computer_systems', 'name': 'Computer Systems'},
        {'id': 'networking', 'name': 'Networking'},
        {'id': 'databases', 'name': 'Databases'},
        {'id': 'theory_of_computation', 'name': 'Theory of Computation'}
    ]
    
    return render_template('admin/create_knowledge_base_entry.html', topics=topics)

@admin_bp.route('/knowledge-base/<int:entry_id>')
@admin_required
def knowledge_base_entry(entry_id):
    """Knowledge base entry details page"""
    # Get knowledge base entry
    entry = KnowledgeBase.query.get_or_404(entry_id)
    
    return render_template('admin/knowledge_base_entry.html', entry=entry)

@admin_bp.route('/knowledge-base/<int:entry_id>/edit', methods=['GET', 'POST'])
@admin_required
def edit_knowledge_base_entry(entry_id):
    """Edit knowledge base entry page"""
    # Get knowledge base entry
    entry = KnowledgeBase.query.get_or_404(entry_id)
    
    if request.method == 'POST':
        # Update knowledge base entry
        entry.topic_id = request.form.get('topic_id')
        entry.title = request.form.get('title')
        entry.content = request.form.get('content')
        entry.source = request.form.get('source')
        
        db.session.commit()
        
        flash('Knowledge base entry updated successfully', 'success')
        return redirect(url_for('admin.knowledge_base_entry', entry_id=entry_id))
    
    # Get topics
    topics = [
        {'id': 'data_types', 'name': 'Data Types'},
        {'id': 'data_structures', 'name': 'Data Structures'},
        {'id': 'algorithms', 'name': 'Algorithms'},
        {'id': 'programming', 'name': 'Programming'},
        {'id': 'computer_systems', 'name': 'Computer Systems'},
        {'id': 'networking', 'name': 'Networking'},
        {'id': 'databases', 'name': 'Databases'},
        {'id': 'theory_of_computation', 'name': 'Theory of Computation'}
    ]
    
    return render_template('admin/edit_knowledge_base_entry.html',
                          entry=entry,
                          topics=topics)

@admin_bp.route('/knowledge-base/<int:entry_id>/delete', methods=['POST'])
@admin_required
def delete_knowledge_base_entry(entry_id):
    """Delete knowledge base entry"""
    # Get knowledge base entry
    entry = KnowledgeBase.query.get_or_404(entry_id)
    
    # Delete knowledge base entry
    db.session.delete(entry)
    db.session.commit()
    
    flash('Knowledge base entry deleted successfully', 'success')
    return redirect(url_for('admin.knowledge_base'))

@admin_bp.route('/stats')
@admin_required
def stats():
    """Statistics page"""
    # Get user count
    user_count = User.query.count()
    
    # Get active subscription count
    active_subscription_count = Subscription.query.filter(
        Subscription.status == 'active'
    ).count()
    
    # Get resource count
    resource_count = Resource.query.count()
    
    # Get knowledge base entry count
    knowledge_base_count = KnowledgeBase.query.count()
    
    # Get user registration stats by month
    user_stats = db.session.query(
        db.func.strftime('%Y-%m', User.created_at).label('month'),
        db.func.count(User.id).label('count')
    ).group_by('month').order_by('month').all()
    
    # Get subscription stats by month
    subscription_stats = db.session.query(
        db.func.strftime('%Y-%m', Subscription.created_at).label('month'),
        db.func.count(Subscription.id).label('count')
    ).group_by('month').order_by('month').all()
    
    return render_template('admin/stats.html',
                          user_count=user_count,
                          active_subscription_count=active_subscription_count,
                          resource_count=resource_count,
                          knowledge_base_count=knowledge_base_count,
                          user_stats=user_stats,
                          subscription_stats=subscription_stats)
