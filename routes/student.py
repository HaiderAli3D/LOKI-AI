"""
Student routes for OCR A-Level Computer Science AI Tutor
"""
from flask import render_template, redirect, url_for, request, flash, jsonify, current_app, abort
from flask_login import login_required, current_user
from routes import student_bp
from models.session import Session
from models.message import Message
from models.topic_progress import TopicProgress
from models.exam_practice import ExamPractice
from models.resource import Resource
from services.claude_service import ClaudeService
from config.database_config import db
from datetime import datetime
import json

# Decorator to check if user has active subscription
def subscription_required(f):
    """Decorator to check if user has active subscription"""
    def decorated_function(*args, **kwargs):
        if not current_user.has_active_subscription():
            flash('You need an active subscription to access this page', 'warning')
            return redirect(url_for('subscription.plans'))
        return f(*args, **kwargs)
    decorated_function.__name__ = f.__name__
    return login_required(decorated_function)

@student_bp.route('/dashboard')
@login_required
def dashboard():
    """Student dashboard"""
    # Get progress summary
    progress_summary = TopicProgress.get_user_progress_summary(current_user.id)
    
    # Get recent sessions
    recent_sessions = current_user.get_recent_sessions()
    
    # Get exam practice stats
    exam_stats = ExamPractice.get_user_exam_practice_stats(current_user.id)
    
    # Get subscription status
    has_subscription = current_user.has_active_subscription()
    subscription = current_user.subscription
    
    # Get topics
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
            topic['last_studied'] = progress.last_studied
        else:
            topic['progress'] = 0
            topic['last_studied'] = None
    
    return render_template('student/dashboard.html',
                          topics=topics,
                          progress_summary=progress_summary,
                          recent_sessions=recent_sessions,
                          exam_stats=exam_stats,
                          has_subscription=has_subscription,
                          subscription=subscription)

@student_bp.route('/topic/<topic_id>')
@subscription_required
def topic(topic_id):
    """Topic page"""
    # Get topic progress
    progress = current_user.get_topic_progress(topic_id)
    
    # Get topic name
    topic_name = progress.get_topic_name()
    
    # Get resources for topic
    resources = Resource.get_resources_by_topic(topic_id)
    
    # Get recent sessions for topic
    recent_sessions = Session.query.filter_by(
        user_id=current_user.id,
        topic_id=topic_id
    ).order_by(Session.start_time.desc()).limit(5).all()
    
    # Get exam practices for topic
    exam_practices = ExamPractice.query.filter_by(
        user_id=current_user.id,
        topic_id=topic_id,
        completed=True
    ).order_by(ExamPractice.start_time.desc()).limit(5).all()
    
    return render_template('student/topic.html',
                          topic_id=topic_id,
                          topic_name=topic_name,
                          progress=progress,
                          resources=resources,
                          recent_sessions=recent_sessions,
                          exam_practices=exam_practices)

@student_bp.route('/progress')
@login_required
def progress():
    """Progress page"""
    # Get all topic progress
    topic_progress = TopicProgress.get_user_progress(current_user.id)
    
    # Get progress summary
    progress_summary = TopicProgress.get_user_progress_summary(current_user.id)
    
    # Get exam practice stats
    exam_stats = ExamPractice.get_user_exam_practice_stats(current_user.id)
    
    # Get recent sessions
    recent_sessions = current_user.get_recent_sessions()
    
    return render_template('student/progress.html',
                          topic_progress=topic_progress,
                          progress_summary=progress_summary,
                          exam_stats=exam_stats,
                          recent_sessions=recent_sessions)

@student_bp.route('/session/start', methods=['POST'])
@subscription_required
def start_session():
    """Start a new learning session"""
    # Get topic ID and mode from form
    topic_id = request.form.get('topic_id')
    mode = request.form.get('mode')
    
    if not topic_id or not mode:
        flash('Topic ID and mode are required', 'danger')
        return redirect(url_for('student.dashboard'))
    
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
    Message(session_id=session.id, role='system', content=system_prompt)
    
    # Add welcome message
    topic_name = progress.get_topic_name()
    welcome_message = f"Welcome to the {topic_name} {mode.capitalize()} session. How can I help you today?"
    
    ClaudeService.create_message(session.id, 'assistant', welcome_message)
    
    # Redirect to session page
    return redirect(url_for('student.session', session_id=session.id))

@student_bp.route('/session/<int:session_id>')
@subscription_required
def session(session_id):
    """Session page"""
    # Get session
    session = Session.query.get_or_404(session_id)
    
    # Check if session belongs to user
    if session.user_id != current_user.id:
        abort(403)
    
    # Get messages
    messages = Message.query.filter_by(session_id=session_id).order_by(Message.timestamp).all()
    
    # Get topic progress
    progress = None
    if session.topic_id:
        progress = current_user.get_topic_progress(session.topic_id)
    
    return render_template('student/session.html',
                          session=session,
                          messages=messages,
                          progress=progress)

@student_bp.route('/session/<int:session_id>/message', methods=['POST'])
@subscription_required
def send_message(session_id):
    """Send a message in a session"""
    # Get session
    session = Session.query.get_or_404(session_id)
    
    # Check if session belongs to user
    if session.user_id != current_user.id:
        return jsonify({'error': 'Unauthorized'}), 403
    
    # Get message content
    content = request.form.get('content')
    
    if not content:
        return jsonify({'error': 'Message content is required'}), 400
    
    # Send message to Claude
    response = ClaudeService.send_message(session_id, content)
    
    if not response:
        return jsonify({'error': 'Error sending message'}), 500
    
    return jsonify(response)

@student_bp.route('/session/<int:session_id>/end', methods=['POST'])
@subscription_required
def end_session(session_id):
    """End a session"""
    # Get session
    session = Session.query.get_or_404(session_id)
    
    # Check if session belongs to user
    if session.user_id != current_user.id:
        abort(403)
    
    # Get proficiency after
    proficiency_after = request.form.get('proficiency_after')
    
    if proficiency_after:
        try:
            proficiency_after = int(proficiency_after)
        except ValueError:
            proficiency_after = None
    
    # End session
    session.end(proficiency_after)
    
    # Redirect to topic page
    if session.topic_id:
        return redirect(url_for('student.topic', topic_id=session.topic_id))
    else:
        return redirect(url_for('student.dashboard'))

@student_bp.route('/exam/start', methods=['POST'])
@subscription_required
def start_exam():
    """Start a new exam practice"""
    # Get topic ID from form
    topic_id = request.form.get('topic_id')
    
    if not topic_id:
        flash('Topic ID is required', 'danger')
        return redirect(url_for('student.dashboard'))
    
    # Generate exam questions
    questions = ClaudeService.generate_exam_questions(topic_id)
    
    if not questions:
        flash('Error generating exam questions', 'danger')
        return redirect(url_for('student.topic', topic_id=topic_id))
    
    # Create exam practice
    exam_practice = ExamPractice(
        user_id=current_user.id,
        topic_id=topic_id,
        questions=questions
    )
    
    db.session.add(exam_practice)
    db.session.commit()
    
    # Redirect to exam page
    return redirect(url_for('student.exam', exam_id=exam_practice.id))

@student_bp.route('/exam/<int:exam_id>')
@subscription_required
def exam(exam_id):
    """Exam page"""
    # Get exam practice
    exam_practice = ExamPractice.query.get_or_404(exam_id)
    
    # Check if exam belongs to user
    if exam_practice.user_id != current_user.id:
        abort(403)
    
    # Get questions and answers
    questions = exam_practice.get_questions()
    answers = exam_practice.get_answers()
    
    # Get topic progress
    progress = None
    if exam_practice.topic_id:
        progress = current_user.get_topic_progress(exam_practice.topic_id)
    
    return render_template('student/exam.html',
                          exam=exam_practice,
                          questions=questions,
                          answers=answers,
                          progress=progress)

@student_bp.route('/exam/<int:exam_id>/answer', methods=['POST'])
@subscription_required
def submit_answer(exam_id):
    """Submit an answer for an exam question"""
    # Get exam practice
    exam_practice = ExamPractice.query.get_or_404(exam_id)
    
    # Check if exam belongs to user
    if exam_practice.user_id != current_user.id:
        return jsonify({'error': 'Unauthorized'}), 403
    
    # Get question ID and answer
    question_id = request.form.get('question_id')
    answer = request.form.get('answer')
    
    if not question_id or not answer:
        return jsonify({'error': 'Question ID and answer are required'}), 400
    
    # Add answer
    exam_practice.add_answer(question_id, answer)
    
    return jsonify({'success': True})

@student_bp.route('/exam/<int:exam_id>/complete', methods=['POST'])
@subscription_required
def complete_exam(exam_id):
    """Complete an exam practice"""
    # Get exam practice
    exam_practice = ExamPractice.query.get_or_404(exam_id)
    
    # Check if exam belongs to user
    if exam_practice.user_id != current_user.id:
        abort(403)
    
    # Get questions and answers
    questions = exam_practice.get_questions()
    answers = exam_practice.get_answers()
    
    # Check if all questions have been answered
    if len(answers) < len(questions):
        flash('Please answer all questions before completing the exam', 'warning')
        return redirect(url_for('student.exam', exam_id=exam_id))
    
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
    
    # Redirect to exam results page
    return redirect(url_for('student.exam_results', exam_id=exam_id))

@student_bp.route('/exam/<int:exam_id>/results')
@subscription_required
def exam_results(exam_id):
    """Exam results page"""
    # Get exam practice
    exam_practice = ExamPractice.query.get_or_404(exam_id)
    
    # Check if exam belongs to user
    if exam_practice.user_id != current_user.id:
        abort(403)
    
    # Check if exam is completed
    if not exam_practice.completed:
        flash('Exam not completed yet', 'warning')
        return redirect(url_for('student.exam', exam_id=exam_id))
    
    # Get questions, answers, and feedback
    questions = exam_practice.get_questions()
    answers = exam_practice.get_answers()
    feedback = exam_practice.get_feedback()
    
    return render_template('student/exam_results.html',
                          exam=exam_practice,
                          questions=questions,
                          answers=answers,
                          feedback=feedback)

@student_bp.route('/resources')
@login_required
def resources():
    """Resources page"""
    # Get topic ID from query parameters
    topic_id = request.args.get('topic_id')
    
    # Get resources
    resources = Resource.get_resources(topic_id)
    
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
    
    return render_template('student/resources.html',
                          resources=resources,
                          topics=topics,
                          selected_topic=topic_id)

@student_bp.route('/resource/<int:resource_id>')
@login_required
def resource(resource_id):
    """Resource page"""
    # Get resource
    resource = Resource.query.get_or_404(resource_id)
    
    # Generate presigned URL if resource has file path
    presigned_url = None
    if resource.file_path:
        from services.aws_service import AWSService
        presigned_url = AWSService.generate_presigned_url(resource.file_path)
    
    return render_template('student/resource.html',
                          resource=resource,
                          presigned_url=presigned_url)
