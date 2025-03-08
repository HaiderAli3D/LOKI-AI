"""
User model for OCR A-Level Computer Science AI Tutor
"""
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import UserMixin
from config.database_config import db

class User(db.Model, UserMixin):
    """User model"""
    
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    firebase_uid = db.Column(db.String(128), unique=True, nullable=True)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=True)
    first_name = db.Column(db.String(50), nullable=False)
    last_name = db.Column(db.String(50), nullable=False)
    role = db.Column(db.String(20), default='student')
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    last_login = db.Column(db.DateTime, nullable=True)
    
    # Relationships
    subscription = db.relationship('Subscription', backref='user', uselist=False, lazy=True)
    sessions = db.relationship('Session', backref='user', lazy=True)
    topic_progress = db.relationship('TopicProgress', backref='user', lazy=True)
    exam_practices = db.relationship('ExamPractice', backref='user', lazy=True)
    
    def __init__(self, email, first_name, last_name, password=None, firebase_uid=None, role='student'):
        """Initialize user"""
        self.email = email
        self.first_name = first_name
        self.last_name = last_name
        self.role = role
        self.firebase_uid = firebase_uid
        
        if password:
            self.set_password(password)
    
    def set_password(self, password):
        """Set password hash"""
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        """Check password hash"""
        if self.password_hash:
            return check_password_hash(self.password_hash, password)
        return False
    
    def update_last_login(self):
        """Update last login timestamp"""
        self.last_login = datetime.utcnow()
        db.session.commit()
    
    def is_admin(self):
        """Check if user is admin"""
        return self.role == 'admin'
    
    def has_active_subscription(self):
        """Check if user has active subscription"""
        return self.subscription is not None and self.subscription.is_active()
    
    def get_subscription_plan(self):
        """Get subscription plan"""
        if self.has_active_subscription():
            return self.subscription.plan
        return None
    
    def get_topic_progress(self, topic_id):
        """Get progress for a specific topic"""
        progress = TopicProgress.query.filter_by(user_id=self.id, topic_id=topic_id).first()
        if not progress:
            progress = TopicProgress(user_id=self.id, topic_id=topic_id)
            db.session.add(progress)
            db.session.commit()
        return progress
    
    def get_recent_sessions(self, limit=5):
        """Get recent learning sessions"""
        return Session.query.filter_by(user_id=self.id).order_by(Session.start_time.desc()).limit(limit).all()
    
    def to_dict(self):
        """Convert user to dictionary"""
        return {
            'id': self.id,
            'email': self.email,
            'first_name': self.first_name,
            'last_name': self.last_name,
            'role': self.role,
            'is_active': self.is_active,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'last_login': self.last_login.isoformat() if self.last_login else None,
            'has_subscription': self.has_active_subscription()
        }
    
    def __repr__(self):
        """String representation of user"""
        return f'<User {self.email}>'
