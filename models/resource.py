"""
Resource model for OCR A-Level Computer Science AI Tutor
"""
from datetime import datetime
import os
from config.database_config import db

class Resource(db.Model):
    """Resource model for learning resources"""
    
    __tablename__ = 'resources'
    
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(255), nullable=False)
    description = db.Column(db.Text, nullable=True)
    file_path = db.Column(db.String(255), nullable=True)
    file_url = db.Column(db.String(255), nullable=True)
    file_type = db.Column(db.String(50), nullable=False)
    topic_id = db.Column(db.String(50), nullable=True)
    is_public = db.Column(db.Boolean, default=True)
    created_by = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def __init__(self, title, file_type, description=None, file_path=None, file_url=None, 
                 topic_id=None, is_public=True, created_by=None):
        """Initialize resource"""
        self.title = title
        self.description = description
        self.file_path = file_path
        self.file_url = file_url
        self.file_type = file_type
        self.topic_id = topic_id
        self.is_public = is_public
        self.created_by = created_by
    
    def get_file_extension(self):
        """Get file extension"""
        if self.file_path:
            return os.path.splitext(self.file_path)[1].lower()
        if self.file_url:
            return os.path.splitext(self.file_url)[1].lower()
        return None
    
    def get_file_size(self):
        """Get file size in bytes"""
        if self.file_path and os.path.exists(self.file_path):
            return os.path.getsize(self.file_path)
        return None
    
    def get_file_location(self):
        """Get file location (path or URL)"""
        return self.file_url or self.file_path
    
    def get_topic_name(self):
        """Get topic name"""
        if not self.topic_id:
            return "General"
        
        # This would typically come from a topics table or service
        # For now, we'll just format the topic_id
        return self.topic_id.replace('_', ' ').title()
    
    def is_downloadable(self):
        """Check if resource is downloadable"""
        return self.file_path is not None or self.file_url is not None
    
    def to_dict(self):
        """Convert resource to dictionary"""
        return {
            'id': self.id,
            'title': self.title,
            'description': self.description,
            'file_path': self.file_path,
            'file_url': self.file_url,
            'file_type': self.file_type,
            'file_extension': self.get_file_extension(),
            'file_size': self.get_file_size(),
            'topic_id': self.topic_id,
            'topic_name': self.get_topic_name(),
            'is_public': self.is_public,
            'created_by': self.created_by,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
            'is_downloadable': self.is_downloadable()
        }
    
    @staticmethod
    def get_resources_by_topic(topic_id=None, is_public=True):
        """Get resources by topic"""
        if topic_id:
            return Resource.query.filter_by(topic_id=topic_id, is_public=is_public).all()
        return Resource.query.filter_by(is_public=is_public).all()
    
    @staticmethod
    def get_resources_by_type(file_type, is_public=True):
        """Get resources by file type"""
        return Resource.query.filter_by(file_type=file_type, is_public=is_public).all()
    
    @staticmethod
    def search_resources(query, is_public=True):
        """Search resources"""
        search_query = f"%{query}%"
        return Resource.query.filter(
            (Resource.title.ilike(search_query) | Resource.description.ilike(search_query)) &
            (Resource.is_public == is_public)
        ).all()
    
    def __repr__(self):
        """String representation of resource"""
        return f'<Resource {self.id} {self.title}>'
