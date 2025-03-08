#!/usr/bin/env python
"""
CLI tool for OCR A-Level Computer Science AI Tutor
"""
import os
import sys
import click
import json
from datetime import datetime
from flask import Flask
from flask.cli import FlaskGroup
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Create Flask app
def create_app():
    from app import app
    return app

@click.group(cls=FlaskGroup, create_app=create_app)
def cli():
    """CLI tool for OCR A-Level Computer Science AI Tutor"""
    pass

@cli.command('create-admin')
@click.argument('email')
@click.argument('password')
@click.argument('first_name')
@click.argument('last_name')
def create_admin(email, password, first_name, last_name):
    """Create an admin user"""
    from models.user import User
    from config.database_config import db
    
    # Check if user already exists
    user = User.query.filter_by(email=email).first()
    if user:
        click.echo(f"User with email {email} already exists")
        return
    
    # Create user
    user = User(
        email=email,
        first_name=first_name,
        last_name=last_name,
        role='admin'
    )
    user.set_password(password)
    
    db.session.add(user)
    db.session.commit()
    
    click.echo(f"Admin user {email} created successfully")

@cli.command('list-users')
def list_users():
    """List all users"""
    from models.user import User
    
    users = User.query.all()
    
    if not users:
        click.echo("No users found")
        return
    
    click.echo(f"Total users: {len(users)}")
    click.echo("ID | Email | Name | Role | Active | Created")
    click.echo("-" * 80)
    
    for user in users:
        click.echo(f"{user.id} | {user.email} | {user.first_name} {user.last_name} | {user.role} | {user.is_active} | {user.created_at}")

@cli.command('list-subscriptions')
def list_subscriptions():
    """List all subscriptions"""
    from models.subscription import Subscription
    from models.user import User
    
    subscriptions = Subscription.query.all()
    
    if not subscriptions:
        click.echo("No subscriptions found")
        return
    
    click.echo(f"Total subscriptions: {len(subscriptions)}")
    click.echo("ID | User | Plan | Status | Current Period End | Canceled")
    click.echo("-" * 80)
    
    for subscription in subscriptions:
        user = User.query.get(subscription.user_id)
        user_email = user.email if user else "Unknown"
        click.echo(f"{subscription.id} | {user_email} | {subscription.plan} | {subscription.status} | {subscription.current_period_end} | {subscription.cancel_at_period_end}")

@cli.command('create-resource')
@click.argument('title')
@click.argument('file_path')
@click.option('--topic-id', help='Topic ID')
@click.option('--description', help='Resource description')
@click.option('--public/--private', default=True, help='Whether the resource is public')
def create_resource(title, file_path, topic_id, description, public):
    """Create a resource from a file"""
    from services.resource_service import ResourceService
    import os
    
    # Check if file exists
    if not os.path.exists(file_path):
        click.echo(f"File not found: {file_path}")
        return
    
    # Get file type
    file_type = os.path.splitext(file_path)[1][1:].lower()
    
    # Open file
    with open(file_path, 'rb') as file:
        # Create resource
        resource = ResourceService.create_resource(
            title=title,
            file=file,
            file_type=file_type,
            description=description,
            topic_id=topic_id,
            is_public=public
        )
        
        if resource:
            click.echo(f"Resource created successfully: {resource.id}")
        else:
            click.echo("Error creating resource")

@cli.command('backup-database')
@click.argument('output_dir', default='backups')
def backup_database(output_dir):
    """Backup database to JSON files"""
    from models.user import User
    from models.subscription import Subscription
    from models.session import Session
    from models.message import Message
    from models.topic_progress import TopicProgress
    from models.exam_practice import ExamPractice
    from models.resource import Resource
    from models.knowledge_base import KnowledgeBase
    
    # Create output directory if it doesn't exist
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
    
    # Create timestamp
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    
    # Backup users
    users = User.query.all()
    user_data = [user.to_dict() for user in users]
    with open(os.path.join(output_dir, f'users_{timestamp}.json'), 'w') as f:
        json.dump(user_data, f, indent=2)
    
    # Backup subscriptions
    subscriptions = Subscription.query.all()
    subscription_data = [subscription.to_dict() for subscription in subscriptions]
    with open(os.path.join(output_dir, f'subscriptions_{timestamp}.json'), 'w') as f:
        json.dump(subscription_data, f, indent=2)
    
    # Backup sessions
    sessions = Session.query.all()
    session_data = [session.to_dict() for session in sessions]
    with open(os.path.join(output_dir, f'sessions_{timestamp}.json'), 'w') as f:
        json.dump(session_data, f, indent=2)
    
    # Backup messages
    messages = Message.query.all()
    message_data = [message.to_dict() for message in messages]
    with open(os.path.join(output_dir, f'messages_{timestamp}.json'), 'w') as f:
        json.dump(message_data, f, indent=2)
    
    # Backup topic progress
    topic_progress = TopicProgress.query.all()
    topic_progress_data = [progress.to_dict() for progress in topic_progress]
    with open(os.path.join(output_dir, f'topic_progress_{timestamp}.json'), 'w') as f:
        json.dump(topic_progress_data, f, indent=2)
    
    # Backup exam practices
    exam_practices = ExamPractice.query.all()
    exam_practice_data = [exam.to_dict() for exam in exam_practices]
    with open(os.path.join(output_dir, f'exam_practices_{timestamp}.json'), 'w') as f:
        json.dump(exam_practice_data, f, indent=2)
    
    # Backup resources
    resources = Resource.query.all()
    resource_data = [resource.to_dict() for resource in resources]
    with open(os.path.join(output_dir, f'resources_{timestamp}.json'), 'w') as f:
        json.dump(resource_data, f, indent=2)
    
    # Backup knowledge base
    knowledge_base = KnowledgeBase.query.all()
    knowledge_base_data = [entry.to_dict() for entry in knowledge_base]
    with open(os.path.join(output_dir, f'knowledge_base_{timestamp}.json'), 'w') as f:
        json.dump(knowledge_base_data, f, indent=2)
    
    click.echo(f"Database backup completed: {output_dir}")

@cli.command('init-db')
def init_db():
    """Initialize database"""
    from config.database_config import db
    
    db.create_all()
    click.echo("Database initialized")

@cli.command('reset-db')
@click.confirmation_option(prompt='Are you sure you want to reset the database?')
def reset_db():
    """Reset database (drop and recreate all tables)"""
    from config.database_config import db
    
    db.drop_all()
    db.create_all()
    click.echo("Database reset")

@cli.command('create-bucket')
def create_bucket():
    """Create S3 bucket"""
    from services.aws_service import AWSService
    
    success = AWSService.create_bucket_if_not_exists()
    
    if success:
        click.echo("S3 bucket created successfully")
    else:
        click.echo("Error creating S3 bucket")

if __name__ == '__main__':
    cli()
