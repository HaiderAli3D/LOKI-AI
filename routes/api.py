"""
API routes for OCR A-Level Computer Science AI Tutor
"""
from flask import request, jsonify, current_app, abort
from flask_login import login_required, current_user
from routes import api_bp
from models.session import Session
from models.message import Message
from models.topic_progress import TopicProgress
from models.exam_practice import ExamPractice
from models.resource import Resource
from services.claude_service import ClaudeService
from config.database_config import db
from functools import wraps
import json

# Decorator to check if user has active subscription
def subscription_required(f):
    """Decorator to check if user has active subscription"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.has_active_subscription():
            return jsonify({'error': 'Subscription required'}), 403
        return f(*args, **kwargs)
    return decorated_function

# Decorator to check if user is admin
def admin_required(f):
    """Decorator to check if user is admin"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_admin():
            return jsonify({'error': 'Admin access required'}), 403
        return f(*args, **kwargs)
    return decorated_function

@api_bp.route('/user')
@login_required
def get_user():
    """Get current user"""
    return jsonify(current_user.to_dict())

@api_bp.route('/subscription')
@login_required
def get_subscription():
    """Get current user's subscription"""
    if current_user.subscription:
        return jsonify(current_user.subscription.to_dict())
    return jsonify(None)

@api_bp.route('/topics')
@login_required
def get_topics():
    """Get topics"""
    topics = [
        {
            'id': 'data_types',
            'name': 'Data Types',
            'description': 'Primitive data types, variables, and constants',
            'icon': 'fas fa-database'
        },
        {
            'id': 'data_structures',
            'name': 'Data Structures',
            'description': 'Arrays, lists, stacks, queues, trees, and graphs',
            'icon': 'fas fa-project-diagram'
        },
        {
            'id': 'algorithms',
            'name': 'Algorithms',
            'description': 'Searching, sorting, and graph algorithms',
            'icon': 'fas fa-code-branch'
        },
        {
            'id': 'programming',
            'name': 'Programming',
            'description': 'Programming concepts and techniques',
            'icon': 'fas fa-code'
        },
        {
            'id': 'computer_systems',
            'name': 'Computer Systems',
            'description': 'Hardware, software, and operating systems',
            'icon': 'fas fa-desktop'
        },
        {
            'id': 'networking',
            'name': 'Networking',
            'description': 'Network protocols, security, and the internet',
            'icon': 'fas fa-network-wired'
        },
        {
            'id': 'databases',
            'name': 'Databases',
            'description': 'Database concepts, SQL, and normalization',
            'icon': 'fas fa-table'
        },
        {
            'id': 'theory_of_computation',
            'name': 'Theory of Computation',
            'description': 'Finite state machines, regular expressions, and Turing machines',
            'icon': 'fas fa-calculator'
        }
    ]
    
    # Get topic progress for each topic
    for topic in topics:
        progress = TopicProgress.get_user_progress_by_topic(current_user.id, topic['id'])
        if progress:
            topic['progress'] = progress.proficiency
            topic['last_studied'] = progress.last_studied.isoformat() if progress.last_studied else None
        else:
            topic['progress'] = 0
            topic['last_studied'] = None
    
    return jsonify(topics)

@api_bp.route('/topic/<topic_id>/progress')
@login_required
def get_topic_progress(topic_id):
    """Get topic progress"""
    progress = current_user.get_topic_progress(topic_id)
    return jsonify(progress.to_dict())

@api_bp.route('/topic/<topic_id>/resources')
@login_required
def get_topic_resources(topic_id):
    """Get topic resources"""
    resources = Resource.get_resources_by_topic(topic_id)
    return jsonify([resource.to_dict() for resource in resources])

@api_bp.route('/sessions')
@login_required
def get_sessions():
    """Get user's sessions"""
    sessions = Session.query.filter_by(user_id=current_user.id).order_by(Session.start_time.desc()).all()
    return jsonify([session.to_dict() for session in sessions])

@api_bp.route('/session/<int:session_id>')
@login_required
def get_session(session_id):
    """Get session"""
    session = Session.query.get_or_404(session_id)
    
    # Check if session belongs to user
    if session.user_id != current_user.id and not current_user.is_admin():
        return jsonify({'error': 'Unauthorized'}), 403
    
    return jsonify(session.to_dict())

@api_bp.route('/session/<int:session_id>/messages')
@login_required
def get_session_messages(session_id):
    """Get session messages"""
    session = Session.query.get_or_404(session_id)
    
    # Check if session belongs to user
    if session.user_id != current_user.id and not current_user.is_admin():
        return jsonify({'error': 'Unauthorized'}), 403
    
    messages = Message.query.filter_by(session_id=session_id).order_by(Message.timestamp).all()
    return jsonify([message.to_dict() for message in messages])

@api_bp.route('/session/start', methods=['POST'])
@subscription_required
def start_session():
    """Start a new learning session"""
    # Get topic ID and mode from request
    data = request.get_json()
    
    if not data:
        return jsonify({'error': 'No data provided'}), 400
    
    topic_id = data.get('topic_id')
    mode = data.get('mode')
    
    if not topic_id or not mode:
        return jsonify({'error': 'Topic ID and mode are required'}), 400
    
    # Get topic progress
    progress = current_user.get_topic_progress(topic_id)
    
    # Create session
    session = Session(
        user_id=current_user.id,
        topic_id=topic_id,
        mode=mode,
        proficiency_before=progress.proficiency
    )
    
    db.session.add(session)
    db.session.commit()
    
    # Add system message
    system_prompt = ClaudeService.get_system_prompt(topic_id, mode)
    ClaudeService.create_message(session.id, 'system', system_prompt)
    
    # Add welcome message
    topic_name = progress.get_topic_name()
    welcome_message = f"Welcome to the {topic_name} {mode.capitalize()} session. How can I help you today?"
    
    ClaudeService.create_message(session.id, 'assistant', welcome_message)
    
    return jsonify(session.to_dict())

@api_bp.route('/session/<int:session_id>/message', methods=['POST'])
@subscription_required
def send_message(session_id):
    """Send a message in a session"""
    # Get session
    session = Session.query.get_or_404(session_id)
    
    # Check if session belongs to user
    if session.user_id != current_user.id:
        return jsonify({'error': 'Unauthorized'}), 403
    
    # Get message content
    data = request.get_json()
    
    if not data:
        return jsonify({'error': 'No data provided'}), 400
    
    content = data.get('content')
    
    if not content:
        return jsonify({'error': 'Message content is required'}), 400
    
    # Send message to Claude
    response = ClaudeService.send_message(session_id, content)
    
    if not response:
        return jsonify({'error': 'Error sending message'}), 500
    
    return jsonify(response)

@api_bp.route('/session/<int:session_id>/end', methods=['POST'])
@subscription_required
def end_session(session_id):
    """End a session"""
    # Get session
    session = Session.query.get_or_404(session_id)
    
    # Check if session belongs to user
    if session.user_id != current_user.id:
        return jsonify({'error': 'Unauthorized'}), 403
    
    # Get proficiency after
    data = request.get_json()
    proficiency_after = data.get('proficiency_after') if data else None
    
    # End session
    session.end(proficiency_after)
    
    return jsonify(session.to_dict())

@api_bp.route('/exam/start', methods=['POST'])
@subscription_required
def start_exam():
    """Start a new exam practice"""
    # Get topic ID from request
    data = request.get_json()
    
    if not data:
        return jsonify({'error': 'No data provided'}), 400
    
    topic_id = data.get('topic_id')
    
    if not topic_id:
        return jsonify({'error': 'Topic ID is required'}), 400
    
    # Generate exam questions
    questions = ClaudeService.generate_exam_questions(topic_id)
    
    if not questions:
        return jsonify({'error': 'Error generating exam questions'}), 500
    
    # Create exam practice
    exam_practice = ExamPractice(
        user_id=current_user.id,
        topic_id=topic_id,
        questions=questions
    )
    
    db.session.add(exam_practice)
    db.session.commit()
    
    return jsonify(exam_practice.to_dict())

@api_bp.route('/exam/<int:exam_id>')
@subscription_required
def get_exam(exam_id):
    """Get exam practice"""
    # Get exam practice
    exam_practice = ExamPractice.query.get_or_404(exam_id)
    
    # Check if exam belongs to user
    if exam_practice.user_id != current_user.id and not current_user.is_admin():
        return jsonify({'error': 'Unauthorized'}), 403
    
    return jsonify(exam_practice.to_dict())

@api_bp.route('/exam/<int:exam_id>/answer', methods=['POST'])
@subscription_required
def submit_answer(exam_id):
    """Submit an answer for an exam question"""
    # Get exam practice
    exam_practice = ExamPractice.query.get_or_404(exam_id)
    
    # Check if exam belongs to user
    if exam_practice.user_id != current_user.id:
        return jsonify({'error': 'Unauthorized'}), 403
    
    # Get question ID and answer
    data = request.get_json()
    
    if not data:
        return jsonify({'error': 'No data provided'}), 400
    
    question_id = data.get('question_id')
    answer = data.get('answer')
    
    if not question_id or not answer:
        return jsonify({'error': 'Question ID and answer are required'}), 400
    
    # Add answer
    exam_practice.add_answer(question_id, answer)
    
    return jsonify({'success': True})

@api_bp.route('/exam/<int:exam_id>/complete', methods=['POST'])
@subscription_required
def complete_exam(exam_id):
    """Complete an exam practice"""
    # Get exam practice
    exam_practice = ExamPractice.query.get_or_404(exam_id)
    
    # Check if exam belongs to user
    if exam_practice.user_id != current_user.id:
        return jsonify({'error': 'Unauthorized'}), 403
    
    # Get questions and answers
    questions = exam_practice.get_questions()
    answers = exam_practice.get_answers()
    
    # Check if all questions have been answered
    if len(answers) < len(questions):
        return jsonify({'error': 'Please answer all questions before completing the exam'}), 400
    
    # Evaluate answers
    feedback = {}
    total_score = 0
    total_marks = 0
    
    for i, question in enumerate(questions):
        question_id = str(i)
        if question_id in answers:
            # Evaluate answer
            evaluation = ClaudeService.evaluate_exam_answer(question, answers[question_id])
            
            if isinstance(evaluation, dict):
                feedback[question_id] = evaluation
                total_score += evaluation.get('score', 0)
                total_marks += evaluation.get('max_score', question.get('marks', 0))
            else:
                # If evaluation failed, use default feedback
                feedback[question_id] = {
                    'score': 0,
                    'max_score': question.get('marks', 0),
                    'feedback': 'Error evaluating answer',
                    'model_answer': question.get('answer', '')
                }
    
    # Calculate percentage score
    percentage_score = (total_score / total_marks * 100) if total_marks > 0 else 0
    
    # Complete exam practice
    exam_practice.complete(feedback, percentage_score)
    
    return jsonify(exam_practice.to_dict())

@api_bp.route('/progress')
@login_required
def get_progress():
    """Get user's progress"""
    # Get all topic progress
    topic_progress = TopicProgress.get_user_progress(current_user.id)
    
    # Get progress summary
    progress_summary = TopicProgress.get_user_progress_summary(current_user.id)
    
    # Get exam practice stats
    exam_stats = ExamPractice.get_user_exam_practice_stats(current_user.id)
    
    return jsonify({
        'topic_progress': [progress.to_dict() for progress in topic_progress],
        'progress_summary': progress_summary,
        'exam_stats': exam_stats
    })

@api_bp.route('/resources')
@login_required
def get_resources():
    """Get resources"""
    # Get topic ID from query parameters
    topic_id = request.args.get('topic_id')
    
    # Get resources
    resources = Resource.get_resources(topic_id)
    
    return jsonify([resource.to_dict() for resource in resources])

@api_bp.route('/resource/<int:resource_id>')
@login_required
def get_resource(resource_id):
    """Get resource"""
    # Get resource
    resource = Resource.query.get_or_404(resource_id)
    
    # Generate presigned URL if resource has file path
    presigned_url = None
    if resource.file_path:
        from services.aws_service import AWSService
        presigned_url = AWSService.generate_presigned_url(resource.file_path)
    
    resource_dict = resource.to_dict()
    resource_dict['presigned_url'] = presigned_url
    
    return jsonify(resource_dict)

@api_bp.route('/search')
@login_required
def search():
    """Search resources and knowledge base"""
    # Get query from query parameters
    query = request.args.get('q')
    
    if not query:
        return jsonify({'error': 'Query is required'}), 400
    
    # Search resources
    resources = Resource.search_resources(query)
    
    # Search knowledge base
    knowledge_base_entries = KnowledgeBase.search_entries(query)
    
    return jsonify({
        'resources': [resource.to_dict() for resource in resources],
        'knowledge_base': [entry.to_dict() for entry in knowledge_base_entries]
    })

@api_bp.route('/stats')
@admin_required
def get_stats():
    """Get statistics"""
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
    
    return jsonify({
        'user_count': user_count,
        'active_subscription_count': active_subscription_count,
        'resource_count': resource_count,
        'knowledge_base_count': knowledge_base_count,
        'user_stats': [{'month': stat[0], 'count': stat[1]} for stat in user_stats],
        'subscription_stats': [{'month': stat[0], 'count': stat[1]} for stat in subscription_stats]
    })
