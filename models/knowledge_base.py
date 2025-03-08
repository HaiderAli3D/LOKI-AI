"""
KnowledgeBase model for OCR A-Level Computer Science AI Tutor
"""
from datetime import datetime
import json
from config.database_config import db

class KnowledgeBase(db.Model):
    """KnowledgeBase model for storing knowledge base entries"""
    
    __tablename__ = 'knowledge_base'
    
    id = db.Column(db.Integer, primary_key=True)
    topic_id = db.Column(db.String(50), nullable=False)
    title = db.Column(db.String(255), nullable=False)
    content = db.Column(db.Text, nullable=False)
    metadata_json = db.Column(db.Text, nullable=True)  # JSON string of metadata
    source = db.Column(db.String(255), nullable=True)
    resource_id = db.Column(db.Integer, db.ForeignKey('resources.id'), nullable=True)
    created_by = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def __init__(self, topic_id, title, content, metadata=None, source=None, resource_id=None, created_by=None):
        """Initialize knowledge base entry"""
        self.topic_id = topic_id
        self.title = title
        self.content = content
        self.metadata_json = json.dumps(metadata) if metadata else None
        self.source = source
        self.resource_id = resource_id
        self.created_by = created_by
    
    def get_metadata(self):
        """Get metadata"""
        if not self.metadata_json:
            return {}
        return json.loads(self.metadata_json)
    
    def set_metadata(self, metadata):
        """Set metadata"""
        self.metadata_json = json.dumps(metadata)
        db.session.commit()
    
    def update_metadata(self, key, value):
        """Update metadata"""
        metadata = self.get_metadata()
        metadata[key] = value
        self.metadata_json = json.dumps(metadata)
        db.session.commit()
    
    def get_topic_name(self):
        """Get topic name"""
        # This would typically come from a topics table or service
        # For now, we'll just format the topic_id
        return self.topic_id.replace('_', ' ').title()
    
    def to_dict(self):
        """Convert knowledge base entry to dictionary"""
        return {
            'id': self.id,
            'topic_id': self.topic_id,
            'topic_name': self.get_topic_name(),
            'title': self.title,
            'content': self.content,
            'metadata': self.get_metadata(),
            'source': self.source,
            'resource_id': self.resource_id,
            'created_by': self.created_by,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }
    
    @staticmethod
    def get_entries_by_topic(topic_id):
        """Get knowledge base entries by topic"""
        return KnowledgeBase.query.filter_by(topic_id=topic_id).all()
    
    @staticmethod
    def search_entries(query):
        """Search knowledge base entries"""
        search_query = f"%{query}%"
        return KnowledgeBase.query.filter(
            KnowledgeBase.title.ilike(search_query) | 
            KnowledgeBase.content.ilike(search_query)
        ).all()
    
    @staticmethod
    def get_entries_for_context(topic_id=None, limit=10):
        """Get knowledge base entries for context"""
        if topic_id:
            return KnowledgeBase.query.filter_by(topic_id=topic_id).order_by(KnowledgeBase.created_at.desc()).limit(limit).all()
        return KnowledgeBase.query.order_by(KnowledgeBase.created_at.desc()).limit(limit).all()
    
    @staticmethod
    def get_context_for_topic(topic_id):
        """Get context for topic"""
        entries = KnowledgeBase.get_entries_by_topic(topic_id)
        context = ""
        
        for entry in entries:
            context += f"# {entry.title}\n\n{entry.content}\n\n"
        
        return context
    
    def __repr__(self):
        """String representation of knowledge base entry"""
        return f'<KnowledgeBase {self.id} {self.topic_id} {self.title}>'
