"""
ExamPractice model for OCR A-Level Computer Science AI Tutor
"""
from datetime import datetime
import json
from config.database_config import db

class ExamPractice(db.Model):
    """ExamPractice model for tracking exam practice sessions"""
    
    __tablename__ = 'exam_practices'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    topic_id = db.Column(db.String(50), nullable=True)
    session_id = db.Column(db.Integer, db.ForeignKey('sessions.id'), nullable=True)
    questions_json = db.Column(db.Text, nullable=False)  # JSON string of questions
    answers_json = db.Column(db.Text, nullable=False)  # JSON string of user answers
    feedback_json = db.Column(db.Text, nullable=True)  # JSON string of feedback
    score = db.Column(db.Float, nullable=True)  # Score as percentage
    completed = db.Column(db.Boolean, default=False)
    start_time = db.Column(db.DateTime, default=datetime.utcnow)
    end_time = db.Column(db.DateTime, nullable=True)
    duration = db.Column(db.Integer, nullable=True)  # Duration in seconds
    
    def __init__(self, user_id, questions, topic_id=None, session_id=None):
        """Initialize exam practice"""
        self.user_id = user_id
        self.topic_id = topic_id
        self.session_id = session_id
        self.questions_json = json.dumps(questions)
        self.answers_json = json.dumps({})
    
    def get_questions(self):
        """Get questions"""
        return json.loads(self.questions_json)
    
    def get_answers(self):
        """Get answers"""
        return json.loads(self.answers_json)
    
    def get_feedback(self):
        """Get feedback"""
        if not self.feedback_json:
            return {}
        return json.loads(self.feedback_json)
    
    def add_answer(self, question_id, answer):
        """Add answer"""
        answers = self.get_answers()
        answers[str(question_id)] = answer
        self.answers_json = json.dumps(answers)
        db.session.commit()
    
    def complete(self, feedback, score):
        """Complete exam practice"""
        self.feedback_json = json.dumps(feedback)
        self.score = score
        self.completed = True
        self.end_time = datetime.utcnow()
        self.duration = (self.end_time - self.start_time).total_seconds()
        db.session.commit()
        
        # Update topic progress if topic_id is provided
        if self.topic_id:
            from models.topic_progress import TopicProgress
            
            progress = TopicProgress.query.filter_by(user_id=self.user_id, topic_id=self.topic_id).first()
            if not progress:
                progress = TopicProgress(user_id=self.user_id, topic_id=self.topic_id)
                db.session.add(progress)
            
            # Update proficiency based on score
            if score >= 90:
                new_proficiency = 5
            elif score >= 80:
                new_proficiency = 4
            elif score >= 70:
                new_proficiency = 3
            elif score >= 60:
                new_proficiency = 2
            else:
                new_proficiency = 1
            
            # Only update if new proficiency is higher
            if new_proficiency > progress.proficiency:
                progress.proficiency = new_proficiency
            
            progress.last_studied = self.end_time
            progress.study_time += self.duration
            progress.session_count += 1
            
            db.session.commit()
    
    def get_topic_name(self):
        """Get topic name"""
        if not self.topic_id:
            return "General Exam Practice"
        
        # This would typically come from a topics table or service
        # For now, we'll just format the topic_id
        return self.topic_id.replace('_', ' ').title()
    
    def to_dict(self):
        """Convert exam practice to dictionary"""
        return {
            'id': self.id,
            'user_id': self.user_id,
            'topic_id': self.topic_id,
            'topic_name': self.get_topic_name(),
            'session_id': self.session_id,
            'questions': self.get_questions(),
            'answers': self.get_answers(),
            'feedback': self.get_feedback(),
            'score': self.score,
            'completed': self.completed,
            'start_time': self.start_time.isoformat() if self.start_time else None,
            'end_time': self.end_time.isoformat() if self.end_time else None,
            'duration': self.duration
        }
    
    @staticmethod
    def get_user_exam_practices(user_id, limit=None):
        """Get exam practices for a user"""
        query = ExamPractice.query.filter_by(user_id=user_id).order_by(ExamPractice.start_time.desc())
        
        if limit:
            query = query.limit(limit)
            
        return query.all()
    
    @staticmethod
    def get_user_exam_practice_stats(user_id):
        """Get exam practice stats for a user"""
        practices = ExamPractice.query.filter_by(user_id=user_id, completed=True).all()
        
        if not practices:
            return {
                'total_practices': 0,
                'average_score': 0,
                'total_questions': 0,
                'total_duration': 0
            }
        
        total_practices = len(practices)
        average_score = sum(p.score for p in practices) / total_practices if total_practices > 0 else 0
        total_questions = sum(len(json.loads(p.questions_json)) for p in practices)
        total_duration = sum(p.duration for p in practices if p.duration) or 0
        
        return {
            'total_practices': total_practices,
            'average_score': average_score,
            'total_questions': total_questions,
            'total_duration': total_duration
        }
    
    def __repr__(self):
        """String representation of exam practice"""
        return f'<ExamPractice {self.id} {self.topic_id} {self.score}>'
