"""
Message model for OCR A-Level Computer Science AI Tutor
"""
from datetime import datetime
from config.database_config import db

class Message(db.Model):
    """Message model for chat messages in learning sessions"""
    
    __tablename__ = 'messages'
    
    id = db.Column(db.Integer, primary_key=True)
    session_id = db.Column(db.Integer, db.ForeignKey('sessions.id'), nullable=False)
    role = db.Column(db.String(20), nullable=False)  # 'user', 'assistant', 'system'
    content = db.Column(db.Text, nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    
    def __init__(self, session_id, role, content):
        """Initialize message"""
        self.session_id = session_id
        self.role = role
        self.content = content
    
    def to_dict(self):
        """Convert message to dictionary"""
        return {
            'id': self.id,
            'session_id': self.session_id,
            'role': self.role,
            'content': self.content,
            'timestamp': self.timestamp.isoformat() if self.timestamp else None
        }
    
    def to_anthropic_message(self):
        """Convert message to Anthropic message format"""
        role_map = {
            'user': 'user',
            'assistant': 'assistant',
            'system': 'system'
        }
        
        return {
            'role': role_map.get(self.role, self.role),
            'content': self.content
        }
    
    @staticmethod
    def get_conversation_history(session_id, limit=None):
        """Get conversation history for a session"""
        query = Message.query.filter_by(session_id=session_id).order_by(Message.timestamp)
        
        if limit:
            query = query.limit(limit)
            
        return query.all()
    
    @staticmethod
    def get_anthropic_messages(session_id, limit=None):
        """Get messages in Anthropic format for a session"""
        messages = Message.get_conversation_history(session_id, limit)
        return [message.to_anthropic_message() for message in messages]
    
    def __repr__(self):
        """String representation of message"""
        return f'<Message {self.id} {self.role}>'
