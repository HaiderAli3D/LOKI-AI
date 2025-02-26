#!/usr/bin/env python3
"""
OCR A-Level Computer Science AI Tutor Web Interface

This web interface extends the command-line application to provide:
1. Admin interface for managing learning resources and files
2. User interface for students to interact with the AI tutor
3. Behind-the-scenes file processing and knowledge base management
"""

from flask import Flask, render_template, request, redirect, url_for, session, jsonify, flash, send_from_directory
import os
import json
import anthropic
import sqlite3
import hashlib
import shutil
from datetime import datetime
from dotenv import load_dotenv
from functools import wraps

# Import existing classes from the command-line application
from Claude_CS_Test import ResourceManager, OCRCSDatabase, OCR_CS_CURRICULUM, OCR_CS_DETAILED_TOPICS, LEARNING_MODES

# Initialize Flask application
app = Flask(__name__)
app.secret_key = os.getenv("FLASK_SECRET_KEY", "ocr_cs_tutor_secret_key")  # Change in production

# Initialize resource manager and database
# We'll create these per request to avoid thread safety issues with SQLite
resource_manager = None
db = None

# Create a function to get the resource manager
def get_resource_manager():
    """Get a resource manager instance for the current request."""
    global resource_manager
    if resource_manager is None:
        resource_manager = ResourceManager()
    return resource_manager

# Create a function to get the database
def get_db():
    """Get a database instance for the current request."""
    global db
    if db is None:
        db = OCRCSDatabase()
    return db

# Register teardown function to close connections
@app.teardown_appcontext
def close_connections(exception):
    """Close database connections when the request ends."""
    global resource_manager, db
    if resource_manager is not None:
        resource_manager.close()
        resource_manager = None
    if db is not None:
        db.close()
        db = None

# Load environment variables
load_dotenv()

# Set up Anthropic API client
def get_anthropic_client():
    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key:
        raise ValueError("ANTHROPIC_API_KEY environment variable is not set")
    return anthropic.Anthropic(api_key=api_key)

# Authentication decorator
def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not session.get('is_admin'):
            flash('Admin access required', 'error')
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

# Create system prompt for Claude
def create_system_prompt():
    """Create a specialized system prompt for the OCR CS tutor."""
    system_prompt = """
    You are an expert OCR A-Level Computer Science tutor with extensive knowledge of the H446 specification and examination standards. Your purpose is to help students understand complex computer science concepts, practice their skills, and prepare for their examinations.

    TEACHING APPROACH:
    - Start with clear, concise definitions of key concepts
    - Break down complex topics into manageable, logical steps
    - Use brief analogies and examples to illustrate concepts
    - Provide short code examples where relevant
    - Focus on essential information and core concepts
    - Use bullet points and numbered lists for clarity
    - Keep explanations concise and to the point
    
    OCR A-LEVEL CURRICULUM AREAS:
    - Computer Systems (Component 01): processors, software development, data exchange, data types/structures, legal/ethical issues
    - Algorithms and Programming (Component 02): computational thinking, problem-solving, programming techniques, standard algorithms
    - Programming Project (Component 03/04): analysis, design, development, testing, evaluation
    
    RESPONSE LENGTH:
    - Keep responses brief and focused
    - Aim for 300-500 words per response
    - Prioritize clarity and precision over exhaustive detail
    - Use bullet points instead of paragraphs when possible
    
    RESPONSE FORMAT:
    - Use markdown formatting for clarity
    - Structure explanations with clear headings
    - Include only essential code examples
    - End with 2-3 key summary points

    Always maintain a supportive, efficient tone. Your goal is to build the student's confidence and competence in computer science according to the OCR A-Level specification while respecting their time.
    """
    return system_prompt.strip()

# Get response from Claude
def get_claude_response(prompt, conversation_history=None, topic_code=None):
    """Get a response from Claude based on the prompt, conversation history, and knowledge base."""
    try:
        client = get_anthropic_client()
        
        messages = []
        
        # Include conversation history if provided
        if conversation_history:
            messages = conversation_history.copy()
        
        # Augment prompt with knowledge base information if available
        augmented_prompt = prompt
        if topic_code and resource_manager:
            knowledge = resource_manager.get_knowledge_for_topic(topic_code)
            
            if knowledge:
                # Summarize knowledge to avoid exceeding context limits
                knowledge_text = "\n\n".join(knowledge)
                if len(knowledge_text) > 10000:  # Limit knowledge text size
                    knowledge_text = knowledge_text[:10000] + "..."
                
                augmented_prompt = f"""
                [REFERENCE INFORMATION]
                The following information is from OCR A-Level Computer Science resources related to topic {topic_code}:
                
                {knowledge_text}
                
                [END REFERENCE INFORMATION]
                
                STUDENT QUESTION:
                {prompt}
                
                Please use the reference information where appropriate to give an accurate, specification-aligned response.
                """
        
        # Add the current prompt
        messages.append({"role": "user", "content": augmented_prompt})
        
        # Create a message and get the response
        response = client.messages.create(
            model="claude-3-5-haiku-20241022",
            max_tokens=2048,
            temperature=0.7,
            system=create_system_prompt(),
            messages=messages
        )
        
        # Get the response text
        response_text = response.content[0].text
        
        return response_text
        
    except anthropic.RateLimitError:
        return "I've reached my rate limit. Please wait a moment before trying again."
    except Exception as e:
        print(f"Error: {str(e)}")
        return "Sorry, I couldn't generate a response at this time."

# Create initial prompt based on topic and mode
def create_initial_prompt(component, main_topic, detailed_topic, mode):
    """Create an initial prompt based on selected component, topic, subtopic, and learning mode."""
    component_title = OCR_CS_CURRICULUM[component]['title']
    
    if mode == "explore":
        return f"""
        I'd like to learn about {detailed_topic} from the OCR A-Level Computer Science curriculum ({component_title}). 
        
        Please provide a comprehensive explanation that:
        1. Starts with a clear definition of the key concepts
        2. Explains the principles in detail, with a logical progression from basic to advanced
        3. Includes practical examples that illustrate the concepts
        4. Relates the topic to the OCR A-Level specification requirements
        5. Highlights any common misconceptions or areas students typically find challenging
        
        Present the information in a clear, methodical structure with appropriate headings and subheadings.
        """
    elif mode == "practice":
        return f"""
        I'd like to practice {detailed_topic} from the OCR A-Level Computer Science curriculum ({component_title}).
        
        Please provide a set of practice questions that:
        1. Start with 1-2 basic knowledge recall questions
        2. Follow with 2-3 application questions of medium difficulty
        3. Include 1-2 higher-level analysis/evaluation questions (similar to exam questions)
        4. Match the style and format of OCR exam questions
        
        Wait for my answer to each question before proceeding to the next one. After each answer, provide detailed feedback explaining the correct approach and marking criteria.
        """
    elif mode == "code":
        return f"""
        I'd like to learn about {detailed_topic} from the OCR A-Level Computer Science curriculum ({component_title}) through practical coding examples.
        
        Please provide:
        1. Code examples that demonstrate the key programming concepts related to this topic
        2. A step-by-step explanation of the code, explaining each section clearly
        3. Common coding patterns and techniques related to this topic
        4. Practical exercises I can try, with gradually increasing complexity
        
        Use pseudocode and/or Python for the examples, matching the style used in OCR exam questions.
        """
    elif mode == "review":
        return f"""
        I'd like to review {detailed_topic} from the OCR A-Level Computer Science curriculum ({component_title}).
        
        Please create a comprehensive revision summary that:
        1. Outlines all the key points and concepts that I need to know
        2. Highlights the most important information for exam purposes
        3. Provides a concise reference list of definitions, algorithms, or formulas
        4. Indicates connections with other parts of the specification
        5. Includes quick recall questions to test my understanding
        
        Structure this as a revision guide with clear sections and bullet points where appropriate.
        """
    elif mode == "test":
        return f"""
        I'd like to test my knowledge of {detailed_topic} from the OCR A-Level Computer Science curriculum ({component_title}).
        
        Please create a mini-assessment with:
        1. 4-6 exam-style questions covering different aspects of this topic
        2. A mix of question types including short answer and extended response
        3. Questions that match the OCR examination style and format
        4. Clear marking scheme and grade boundaries
        
        Present all questions at once, then wait for my complete submission before providing feedback and a grade.
        """
    else:
        return f"I'd like to learn about {detailed_topic} from the OCR A-Level Computer Science curriculum ({component_title}). Please help me understand this topic in detail."

# Routes
@app.route('/')
def index():
    """Home page with options to enter as admin or student."""
    return render_template('index.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    """Login page for admin access."""
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        # For development - use environment variables in production
        admin_username = os.environ.get('ADMIN_USERNAME', 'admin')
        admin_password = os.environ.get('ADMIN_PASSWORD', 'password')
        
        # Simple authentication
        if username == admin_username and password == admin_password:
            session['is_admin'] = True
            return redirect(url_for('admin_dashboard'))
        else:
            flash('Invalid credentials', 'error')
            
    return render_template('login.html')

@app.route('/logout')
def logout():
    """Logout user."""
    session.clear()
    return redirect(url_for('index'))

# Admin routes
@app.route('/admin/dashboard')
@admin_required
def admin_dashboard():
    """Admin dashboard."""
    return render_template('admin/dashboard.html')

@app.route('/admin/resources')
@admin_required
def admin_resources():
    """View all resources."""
    rm = get_resource_manager()
    files = rm.get_all_file_info()
    return render_template('admin/resources.html', files=files)

@app.route('/admin/upload', methods=['GET', 'POST'])
@admin_required
def admin_upload():
    """Upload resources."""
    if request.method == 'POST':
        if 'file' not in request.files:
            flash('No file part', 'error')
            return redirect(request.url)
            
        file = request.files['file']
        if file.filename == '':
            flash('No selected file', 'error')
            return redirect(request.url)
            
        if file:
            # Save file temporarily
            temp_path = os.path.join('/tmp', file.filename)
            file.save(temp_path)
            
            # Process file
            rm = get_resource_manager()
            file_id = rm.add_file(temp_path)
            if file_id:
                rm.process_file_content(file_id)
                flash('File processed successfully', 'success')
            else:
                flash('File already exists or could not be processed', 'warning')
                
            # Remove temporary file
            os.remove(temp_path)
            
            return redirect(url_for('admin_resources'))
            
    return render_template('admin/upload.html')

# Student routes
@app.route('/student/dashboard')
def student_dashboard():
    """Student dashboard with topic selection."""
    return render_template('student/dashboard.html', 
                          curriculum=OCR_CS_CURRICULUM,
                          detailed_topics=OCR_CS_DETAILED_TOPICS)

@app.route('/student/topic/<component>/<topic_code>')
def student_topic(component, topic_code):
    """Topic learning page."""
    # Find the topic title
    topic_title = None
    for topic in OCR_CS_CURRICULUM[component]['topics']:
        if topic.startswith(topic_code):
            topic_title = topic
            break
    
    # If it's a detailed topic, get the title from detailed topics
    if not topic_title and topic_code in OCR_CS_DETAILED_TOPICS:
        topic_title = OCR_CS_DETAILED_TOPICS[topic_code]['title']
    
    return render_template('student/topic.html', 
                          component=component, 
                          topic_code=topic_code,
                          topic_title=topic_title,
                          learning_modes=LEARNING_MODES)

@app.route('/student/initial-prompt', methods=['POST'])
def student_initial_prompt():
    """API endpoint for getting initial prompt based on topic and mode."""
    try:
        data = request.json
        topic_code = data.get('topic_code')
        mode = data.get('mode', 'explore')
        
        # Find the component and topic
        component = None
        main_topic = None
        detailed_topic = None
        
        # Search for the topic in the curriculum
        for comp, info in OCR_CS_CURRICULUM.items():
            for topic in info['topics']:
                if topic.startswith(topic_code):
                    component = comp
                    main_topic = topic
                    detailed_topic = topic
                    break
            if component:
                break
        
        # If it's a detailed topic, get it from detailed topics
        if not component and topic_code in OCR_CS_DETAILED_TOPICS:
            # Find the parent topic
            parent_code = '.'.join(topic_code.split('.')[:2])
            for comp, info in OCR_CS_CURRICULUM.items():
                for topic in info['topics']:
                    if topic.startswith(parent_code):
                        component = comp
                        main_topic = topic
                        detailed_topic = topic_code + ' ' + OCR_CS_DETAILED_TOPICS[topic_code]['title']
                        break
                if component:
                    break
        
        if not component or not main_topic:
            return jsonify({'error': 'Topic not found'})
        
        # Create initial prompt
        initial_prompt = create_initial_prompt(component, main_topic, detailed_topic, mode)
        
        # Check if ANTHROPIC_API_KEY is set
        api_key = os.getenv("ANTHROPIC_API_KEY")
        if not api_key:
            return jsonify({'error': 'ANTHROPIC_API_KEY is not set. Please set it in the environment variables.'}), 500
        
        # Get response from Claude
        response = get_claude_response(initial_prompt, topic_code=topic_code)
        
        # Start a new session in the database
        database = get_db()
        session_id = database.start_session([component, main_topic, detailed_topic])
        
        # Store session ID in Flask session
        session['db_session_id'] = session_id
        session['current_topic'] = main_topic
        session['current_detailed_topic'] = detailed_topic
        
        # Add messages to database
        database.add_message(session_id, "user", initial_prompt)
        database.add_message(session_id, "assistant", response)
        
        return jsonify({'response': response})
    except Exception as e:
        print(f"Error in student_initial_prompt: {str(e)}")
        return jsonify({'error': f'Error generating initial response: {str(e)}'}), 500

@app.route('/student/chat', methods=['POST'])
def student_chat():
    """API endpoint for chat interactions."""
    try:
        data = request.json
        question = data.get('question')
        topic_code = data.get('topic_code')
        mode = data.get('mode', 'explore')
        
        # Get session ID from Flask session
        session_id = session.get('db_session_id')
        
        # Get conversation history from database
        database = get_db()
        conversation_history = []
        if session_id:
            messages = database.get_session_messages(session_id)
            for _, role, content in messages:
                conversation_history.append({"role": role, "content": content})
        
        # Check if ANTHROPIC_API_KEY is set
        api_key = os.getenv("ANTHROPIC_API_KEY")
        if not api_key:
            return jsonify({'error': 'ANTHROPIC_API_KEY is not set. Please set it in the environment variables.'}), 500
        
        # Get response from Claude
        response = get_claude_response(question, conversation_history, topic_code)
        
        # Add messages to database
        if session_id:
            database.add_message(session_id, "user", question)
            database.add_message(session_id, "assistant", response)
        
        return jsonify({'response': response})
    except Exception as e:
        print(f"Error in student_chat: {str(e)}")
        return jsonify({'error': f'Error generating response: {str(e)}'}), 500

@app.route('/student/progress')
def student_progress():
    """View student progress."""
    database = get_db()
    topic_progress = database.get_topic_progress()
    exam_progress = database.get_exam_progress()
    return render_template('student/progress.html', 
                          topic_progress=topic_progress,
                          exam_progress=exam_progress)

@app.route('/student/rate-topic', methods=['POST'])
def student_rate_topic():
    """Rate understanding of a topic."""
    data = request.json
    topic_code = data.get('topic_code')
    topic_title = data.get('topic_title')
    rating = data.get('rating')
    notes = data.get('notes', '')
    
    if not topic_code or not topic_title or not rating:
        return jsonify({'error': 'Missing required fields'})
    
    database = get_db()
    database.update_topic_progress(topic_code, topic_title, rating, notes)
    return jsonify({'success': True})

@app.route('/student/record-exam', methods=['POST'])
def student_record_exam():
    """Record exam practice results."""
    data = request.json
    topic_code = data.get('topic_code')
    question_type = data.get('question_type')
    difficulty = data.get('difficulty')
    score = data.get('score')
    max_score = data.get('max_score')
    
    if not all([topic_code, question_type, difficulty, score, max_score]):
        return jsonify({'error': 'Missing required fields'})
    
    database = get_db()
    database.record_exam_practice(topic_code, question_type, difficulty, score, max_score)
    return jsonify({'success': True})

@app.route('/resources/<path:filename>')
def serve_resource(filename):
    """Serve resource files (PDFs, etc.)."""
    return send_from_directory('resources', filename)

@app.route('/global-chat', methods=['POST'])
def global_chat():
    """API endpoint for general CS questions (not tied to a specific topic)."""
    try:
        data = request.json
        question = data.get('question')
        
        if not question:
            return jsonify({'error': 'No question provided'}), 400
            
        # Create a session key for global chat if it doesn't exist
        if 'global_chat_history' not in session:
            session['global_chat_history'] = []
            
        # Get conversation history from session
        conversation_history = session.get('global_chat_history', [])
        
        # Check if ANTHROPIC_API_KEY is set
        api_key = os.getenv("ANTHROPIC_API_KEY")
        if not api_key:
            return jsonify({'error': 'ANTHROPIC_API_KEY is not set. Please set it in the environment variables.'}), 500
        
        # Create a system prompt specifically for general CS questions
        general_system_prompt = """
        You are an expert OCR A-Level Computer Science tutor. Answer any computer science questions concisely and accurately.
        Focus on OCR A-Level curriculum topics, but be prepared to answer general computer science questions too.
        Keep responses brief (200-300 words) and use bullet points where appropriate.
        Include code examples only when necessary and keep them short.
        End with 1-2 key takeaways.
        """
        
        # Get response from Claude
        client = get_anthropic_client()
        
        # Prepare messages
        messages = []
        for msg in conversation_history:
            messages.append(msg)
            
        # Add the current question
        messages.append({"role": "user", "content": question})
        
        # Create a message and get the response
        response = client.messages.create(
            model="claude-3-5-haiku-20241022",
            max_tokens=1024,
            temperature=0.7,
            system=general_system_prompt,
            messages=messages
        )
        
        # Get the response text
        response_text = response.content[0].text
        
        # Update conversation history (limit to last 10 messages to keep context window manageable)
        conversation_history.append({"role": "user", "content": question})
        conversation_history.append({"role": "assistant", "content": response_text})
        
        # Keep only the last 10 messages
        if len(conversation_history) > 10:
            conversation_history = conversation_history[-10:]
            
        # Update session
        session['global_chat_history'] = conversation_history
        
        return jsonify({'response': response_text})
    except Exception as e:
        print(f"Error in global_chat: {str(e)}")
        return jsonify({'error': f'Error generating response: {str(e)}'}), 500

if __name__ == '__main__':
    app.run(debug=True)
