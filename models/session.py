"""
Session model for OCR A-Level Computer Science AI Tutor
"""
from datetime import datetime
from config.database_config import db

class Session(db.Model):
    """Session model for learning sessions"""
    
    __tablename__ = 'sessions'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    topic_id = db.Column(db.String(50), nullable=True)
    mode = db.Column(db.String(20), nullable=False)
    start_time = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    end_time = db.Column(db.DateTime, nullable=True)
    duration = db.Column(db.Integer, nullable=True)  # Duration in seconds
    proficiency_before = db.Column(db.Integer, nullable=True)
    proficiency_after = db.Column(db.Integer, nullable=True)
    
    # Relationships
    messages = db.relationship('Message', backref='session', lazy=True, cascade='all, delete-orphan')
    
    def __init__(self, user_id, mode, topic_id=None, proficiency_before=None):
        """Initialize session"""
        self.user_id = user_id
        self.mode = mode
        self.topic_id = topic_id
        self.proficiency_before = proficiency_before
    
    def end(self, proficiency_after=None):
        """End session and calculate duration"""
        self.end_time = datetime.utcnow()
        self.duration = (self.end_time - self.start_time).total_seconds()
        self.proficiency_after = proficiency_after
        db.session.commit()
        
        # Update topic progress if topic_id and proficiency_after are provided
        if self.topic_id and self.proficiency_after is not None:
            from models.topic_progress import TopicProgress
            
            progress = TopicProgress.query.filter_by(user_id=self.user_id, topic_id=self.topic_id).first()
            if not progress:
                progress = TopicProgress(user_id=self.user_id, topic_id=self.topic_id)
                db.session.add(progress)
            
            progress.proficiency = self.proficiency_after
            progress.last_studied = self.end_time
            progress.study_time += self.duration
            progress.session_count += 1
            
            db.session.commit()
    
    def add_message(self, role, content):
        """Add message to session"""
        from models.message import Message
        
        message = Message(session_id=self.id, role=role, content=content)
        db.session.add(message)
        db.session.commit()
        return message
    
    def get_messages(self):
        """Get all messages in session"""
        from models.message import Message
        
        return Message.query.filter_by(session_id=self.id).order_by(Message.timestamp).all()
    
    def get_topic_name(self):
        """Get topic name"""
        if not self.topic_id:
            return None
        
        # This would typically come from a topics table or service
        # For now, we'll just format the topic_id
        return self.topic_id.replace('_', ' ').title()
    
    def to_dict(self):
        """Convert session to dictionary"""
        return {
            'id': self.id,
            'user_id': self.user_id,
            'topic_id': self.topic_id,
            'topic_name': self.get_topic_name(),
            'mode': self.mode,
            'start_time': self.start_time.isoformat() if self.start_time else None,
            'end_time': self.end_time.isoformat() if self.end_time else None,
            'duration': self.duration,
            'proficiency_before': self.proficiency_before,
            'proficiency_after': self.proficiency_after,
            'message_count': len(self.messages) if self.messages else 0
        }
    
    def __repr__(self):
        """String representation of session"""
        return f'<Session {self.id} {self.mode} {self.topic_id}>'
