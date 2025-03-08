"""
TopicProgress model for OCR A-Level Computer Science AI Tutor
"""
from datetime import datetime
from config.database_config import db

class TopicProgress(db.Model):
    """TopicProgress model for tracking student progress on topics"""
    
    __tablename__ = 'topic_progress'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    topic_id = db.Column(db.String(50), nullable=False)
    proficiency = db.Column(db.Integer, default=0)  # 0-5 scale
    last_studied = db.Column(db.DateTime, nullable=True)
    study_time = db.Column(db.Integer, default=0)  # Total study time in seconds
    session_count = db.Column(db.Integer, default=0)  # Number of study sessions
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Define a unique constraint on user_id and topic_id
    __table_args__ = (db.UniqueConstraint('user_id', 'topic_id'),)
    
    def __init__(self, user_id, topic_id, proficiency=0):
        """Initialize topic progress"""
        self.user_id = user_id
        self.topic_id = topic_id
        self.proficiency = proficiency
    
    def update_proficiency(self, proficiency):
        """Update proficiency level"""
        self.proficiency = proficiency
        self.last_studied = datetime.utcnow()
        db.session.commit()
    
    def add_study_time(self, seconds):
        """Add study time"""
        self.study_time += seconds
        self.last_studied = datetime.utcnow()
        db.session.commit()
    
    def increment_session_count(self):
        """Increment session count"""
        self.session_count += 1
        self.last_studied = datetime.utcnow()
        db.session.commit()
    
    def get_topic_name(self):
        """Get topic name"""
        # This would typically come from a topics table or service
        # For now, we'll just format the topic_id
        return self.topic_id.replace('_', ' ').title()
    
    def get_proficiency_label(self):
        """Get proficiency label"""
        labels = [
            'Not Started',
            'Beginner',
            'Basic Understanding',
            'Intermediate',
            'Advanced',
            'Expert'
        ]
        return labels[min(self.proficiency, 5)]
    
    def get_proficiency_color(self):
        """Get proficiency color"""
        colors = [
            '#dc3545',  # Red
            '#e05d49',  # Red-Orange
            '#e7854d',  # Orange
            '#eead51',  # Yellow
            '#a3c557',  # Light Green
            '#28a745'   # Green
        ]
        return colors[min(self.proficiency, 5)]
    
    def to_dict(self):
        """Convert topic progress to dictionary"""
        return {
            'id': self.id,
            'user_id': self.user_id,
            'topic_id': self.topic_id,
            'topic_name': self.get_topic_name(),
            'proficiency': self.proficiency,
            'proficiency_label': self.get_proficiency_label(),
            'proficiency_color': self.get_proficiency_color(),
            'last_studied': self.last_studied.isoformat() if self.last_studied else None,
            'study_time': self.study_time,
            'session_count': self.session_count,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }
    
    @staticmethod
    def get_user_progress(user_id):
        """Get all topic progress for a user"""
        return TopicProgress.query.filter_by(user_id=user_id).all()
    
    @staticmethod
    def get_user_progress_by_topic(user_id, topic_id):
        """Get topic progress for a user and topic"""
        return TopicProgress.query.filter_by(user_id=user_id, topic_id=topic_id).first()
    
    @staticmethod
    def get_user_progress_summary(user_id):
        """Get progress summary for a user"""
        progress_list = TopicProgress.query.filter_by(user_id=user_id).all()
        
        total_topics = len(progress_list)
        if total_topics == 0:
            return {
                'total_topics': 0,
                'started_topics': 0,
                'mastered_topics': 0,
                'average_proficiency': 0,
                'total_study_time': 0,
                'total_sessions': 0
            }
        
        started_topics = sum(1 for p in progress_list if p.proficiency > 0)
        mastered_topics = sum(1 for p in progress_list if p.proficiency >= 4)
        average_proficiency = sum(p.proficiency for p in progress_list) / total_topics
        total_study_time = sum(p.study_time for p in progress_list)
        total_sessions = sum(p.session_count for p in progress_list)
        
        return {
            'total_topics': total_topics,
            'started_topics': started_topics,
            'mastered_topics': mastered_topics,
            'average_proficiency': average_proficiency,
            'total_study_time': total_study_time,
            'total_sessions': total_sessions
        }
    
    def __repr__(self):
        """String representation of topic progress"""
        return f'<TopicProgress {self.user_id} {self.topic_id} {self.proficiency}>'
