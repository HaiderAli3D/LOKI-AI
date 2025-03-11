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
import time
from datetime import datetime
from dotenv import load_dotenv
from functools import wraps
from werkzeug.security import generate_password_hash, check_password_hash

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
        print("WARNING: ANTHROPIC_API_KEY environment variable is not set or empty")
        return None
    return anthropic.Anthropic(api_key=api_key)

def is_api_key_set():
    """Check if the Anthropic API key is set."""
    api_key = os.getenv("ANTHROPIC_API_KEY")
    return api_key is not None and api_key.strip() != ""

# Database functions for user management
def init_user_db():
    """Initialize the user database tables if they don't exist."""
    conn = sqlite3.connect('user_database.db')
    cursor = conn.cursor()
    
    # Create users table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY,
        email TEXT UNIQUE NOT NULL,
        password_hash TEXT NOT NULL,
        full_name TEXT NOT NULL,
        role TEXT CHECK(role IN ('student', 'admin')) DEFAULT 'student',
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    ''')
    
    # Modify sessions table to include user_id if it exists
    cursor.execute("PRAGMA table_info(sessions)")
    columns = cursor.fetchall()
    column_names = [col[1] for col in columns]
    
    if 'user_id' not in column_names and columns:
        try:
            cursor.execute("ALTER TABLE sessions ADD COLUMN user_id INTEGER REFERENCES users(id)")
        except sqlite3.Error as e:
            print(f"Error modifying sessions table: {e}")
    
    conn.commit()
    conn.close()

def get_user_by_email(email):
    """Get a user from the database by email."""
    conn = sqlite3.connect('user_database.db')
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM users WHERE email = ?", (email,))
    user = cursor.fetchone()
    conn.close()
    return user

def get_user_by_id(user_id):
    """Get a user from the database by ID."""
    conn = sqlite3.connect('user_database.db')
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM users WHERE id = ?", (user_id,))
    user = cursor.fetchone()
    conn.close()
    return user

def create_user(email, password, full_name, role='student'):
    """Create a new user in the database."""
    conn = sqlite3.connect('user_database.db')
    cursor = conn.cursor()
    
    # Check if user already exists
    cursor.execute("SELECT id FROM users WHERE email = ?", (email,))
    if cursor.fetchone():
        conn.close()
        return False, "Email already registered"
    
    # Hash the password before storing
    password_hash = generate_password_hash(password)
    
    try:
        cursor.execute(
            "INSERT INTO users (email, password_hash, full_name, role) VALUES (?, ?, ?, ?)",
            (email, password_hash, full_name, role)
        )
        conn.commit()
        user_id = cursor.lastrowid
        conn.close()
        return True, user_id
    except Exception as e:
        conn.rollback()
        conn.close()
        return False, str(e)

# Authentication decorators
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not session.get('user_id'):
            flash('Please log in to access this page', 'error')
            return redirect(url_for('student_login'))
        return f(*args, **kwargs)
    return decorated_function

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
    - Strictly use markdown formatting for clarity
    - Structure explanations with clear headings
    - Include only essential code examples
    - End with 2-3 key summary points
    
    CONTEXT TAGS:
    User messages will contain context tags at the end of each message in the format:
    [CONTEXT: {topic_info} | {current_time}]
    
    - For topic-specific chats: [CONTEXT: Topic 1.1.1 Structure and Function of the Processor | 15:30:45]
    - For general learning chat: [CONTEXT: General Learning | 15:30:45]
    
    Use this context information to:
    1. Stay focused on the specific topic the student is learning
    2. Provide time-appropriate responses (e.g., brief responses late at night)
    3. Ensure continuity in the learning session
    4. Tailor examples to the specific topic area
    
    You stay strictly close to the specification and will only respond to computer science related requests. You are to refuse any requests unrelated to A level computer science.
    Never accept unrelated requests that will not help the student achieve a high grade in computer science. Do not accept requests to do tasks for other subjects, do not play games.

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
# Initialize database on startup
def initialize_db():
    """Initialize database tables"""
    init_user_db()

# Function to migrate database schema
def migrate_database():
    """Apply database migrations to add new columns to existing tables"""
    print("Running database migrations...")
    try:
        conn = sqlite3.connect('ocr_cs_tutor.db')
        cursor = conn.cursor()
        
        # Check if user_id column exists in topic_progress table
        cursor.execute("PRAGMA table_info(topic_progress)")
        columns = cursor.fetchall()
        column_names = [col[1] for col in columns]
        
        if 'user_id' not in column_names and columns:
            print("Adding user_id column to topic_progress table")
            cursor.execute("ALTER TABLE topic_progress ADD COLUMN user_id INTEGER")
        
        # Check if user_id column exists in sessions table
        cursor.execute("PRAGMA table_info(sessions)")
        columns = cursor.fetchall()
        column_names = [col[1] for col in columns]
        
        if 'user_id' not in column_names and columns:
            print("Adding user_id column to sessions table")
            cursor.execute("ALTER TABLE sessions ADD COLUMN user_id INTEGER")
        
        # Check if user_id column exists in exam_practice table
        cursor.execute("PRAGMA table_info(exam_practice)")
        columns = cursor.fetchall()
        column_names = [col[1] for col in columns]
        
        if 'user_id' not in column_names and columns:
            print("Adding user_id column to exam_practice table")
            cursor.execute("ALTER TABLE exam_practice ADD COLUMN user_id INTEGER")
        
        conn.commit()
        conn.close()
        print("Database migrations completed successfully")
    except sqlite3.Error as e:
        print(f"Database migration error: {e}")

# Create initialization function for database
with app.app_context():
    initialize_db()
    migrate_database()

@app.route('/')
def index():
    """Home page with feature showcase and options to enter as admin or student."""
    return render_template('index.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    """Registration page for new users."""
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        full_name = request.form.get('full_name')
        
        if not email or not password or not full_name:
            flash('All fields are required', 'error')
            return render_template('register.html')
            
        # Create user
        success, result = create_user(email, password, full_name)
        
        if success:
            # Set session
            session['user_id'] = result
            session['user_email'] = email
            session['user_name'] = full_name
            flash('Registration successful!', 'success')
            return redirect(url_for('student_dashboard'))
        else:
            flash(f'Registration failed: {result}', 'error')
            
    return render_template('register.html')

@app.route('/student/login', methods=['GET', 'POST'])
def student_login():
    """Login page for student access."""
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        
        if not email or not password:
            flash('Email and password are required', 'error')
            return render_template('student/login.html')
            
        # Get user from database
        user = get_user_by_email(email)
        
        if user and check_password_hash(user[2], password):  # Index 2 is password_hash
            # Set session
            session['user_id'] = user[0]  # Index 0 is id
            session['user_email'] = user[1]  # Index 1 is email
            session['user_name'] = user[3]  # Index 3 is full_name
            
            if user[4] == 'admin':  # Index 4 is role
                session['is_admin'] = True
                
            flash('Login successful!', 'success')
            return redirect(url_for('student_dashboard'))
        else:
            flash('Invalid email or password', 'error')
            
    return render_template('student/login.html')

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
    flash('You have been logged out', 'info')
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
        
        files = request.files.getlist('file')
        if not files or files[0].filename == '':
            flash('No selected files', 'error')
            return redirect(request.url)
        
        category = request.form.get('category')
        
        # Process each file
        rm = get_resource_manager()
        processed_count = 0
        duplicate_count = 0
        error_count = 0
        
        for file in files:
            if file.filename == '':
                continue
                
            try:
                # Create a safe filename to avoid path issues
                safe_filename = os.path.basename(file.filename)
                print(f"Processing file: {safe_filename}")
                
                # Create temp directory if it doesn't exist
                temp_dir = os.path.join(os.getcwd(), 'temp_uploads')
                os.makedirs(temp_dir, exist_ok=True)
                
                # Save file temporarily with a unique name to avoid conflicts
                temp_path = os.path.join(temp_dir, f"{int(time.time())}_{safe_filename}")
                file.save(temp_path)
                print(f"File saved to: {temp_path}")
                
                # Process file
                file_id = rm.add_file(temp_path, category)
                print(f"File ID: {file_id}")
                
                if file_id:
                    rm.process_file_content(file_id)
                    processed_count += 1
                else:
                    duplicate_count += 1
                
                # Remove temporary file
                if os.path.exists(temp_path):
                    os.remove(temp_path)
            except Exception as e:
                print(f"Error processing file {file.filename}: {str(e)}")
                error_count += 1
        
        # Flash appropriate message based on results
        if processed_count > 0:
            flash(f'{processed_count} file(s) processed successfully', 'success')
        if duplicate_count > 0:
            flash(f'{duplicate_count} duplicate file(s) skipped', 'warning')
        if error_count > 0:
            flash(f'{error_count} file(s) could not be processed due to errors', 'error')
            
        return redirect(url_for('admin_resources'))
            
    return render_template('admin/upload.html')

# Student routes
@app.route('/student/dashboard')
@login_required
def student_dashboard():
    """Student dashboard with topic selection."""
    return render_template('student/dashboard.html', 
                          curriculum=OCR_CS_CURRICULUM,
                          detailed_topics=OCR_CS_DETAILED_TOPICS,
                          user_name=session.get('user_name'))

@app.route('/student/topic/<component>/<topic_code>')
@login_required
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
                          learning_modes=LEARNING_MODES,
                          user_name=session.get('user_name'))

@app.route('/student/initial-prompt', methods=['POST'])
@login_required
def student_initial_prompt():
    """API endpoint for getting initial prompt based on topic and mode."""
    try:
        data = request.json
        topic_code = data.get('topic_code')
        mode = data.get('mode', 'explore')
        user_id = session.get('user_id')
        
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
        try:
            # Try to use the version with user_id
            session_id = database.start_session([component, main_topic, detailed_topic], user_id=user_id)
        except TypeError:
            # Fall back to original function if user_id parameter doesn't exist
            session_id = database.start_session([component, main_topic, detailed_topic])
            
            # Add monkey patching for basic OCRCSDatabase class to support user verification
            if not hasattr(database, 'verify_session_ownership'):
                def verify_session_ownership(self, session_id, user_id):
                    """Check if a session belongs to a user - basic implementation always returns True."""
                    return True
                database.verify_session_ownership = verify_session_ownership.__get__(database)
        
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
@login_required
def student_chat():
    """API endpoint for chat interactions for the logged-in user."""
    try:
        data = request.json
        question = data.get('question')
        topic_code = data.get('topic_code')
        mode = data.get('mode', 'explore')
        user_id = session.get('user_id')
        
        # Get session ID from Flask session
        session_id = session.get('db_session_id')
        
        # Get conversation history from database
        database = get_db()
        conversation_history = []
        if session_id:
            # Verify this session belongs to the current user
            if database.verify_session_ownership(session_id, user_id):
                messages = database.get_session_messages(session_id)
                for _, role, content in messages:
                    conversation_history.append({"role": role, "content": content})
            else:
                return jsonify({'error': 'Session not found or unauthorized'}), 403
        
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
@login_required
def student_progress():
    """View student progress for the logged-in user."""
    user_id = session.get('user_id')
    database = get_db()
    
    try:
        # Try to filter by user_id
        topic_progress = database.get_topic_progress(user_id=user_id)
        exam_progress = database.get_exam_progress(user_id=user_id)
    except (sqlite3.OperationalError, TypeError) as e:
        # Fallback if we get "no such column" error or TypeError (when function doesn't accept user_id parameter)
        if isinstance(e, sqlite3.OperationalError) and "no such column: user_id" in str(e):
            print(f"Warning: User ID column missing - using unfiltered data: {e}")
        elif isinstance(e, TypeError):
            print(f"Warning: Database function doesn't accept user_id parameter: {e}")
        # Fallback to unfiltered data
        topic_progress = database.get_topic_progress()
        exam_progress = database.get_exam_progress()
    except Exception as e:
        # Re-raise if it's some other error
        print(f"Error in student_progress: {e}")
        raise
    
    return render_template('student/progress.html', 
                          topic_progress=topic_progress,
                          exam_progress=exam_progress,
                          user_name=session.get('user_name'))

@app.route('/student/rate-topic', methods=['POST'])
@login_required
def student_rate_topic():
    """Rate understanding of a topic for the logged-in user."""
    data = request.json
    user_id = session.get('user_id')
    topic_code = data.get('topic_code')
    topic_title = data.get('topic_title')
    rating = data.get('rating')
    notes = data.get('notes', '')
    
    if not topic_code or not topic_title or not rating:
        return jsonify({'error': 'Missing required fields'})
    
    database = get_db()
    try:
        # Try to update with user_id
        database.update_topic_progress(topic_code, topic_title, rating, notes, user_id=user_id)
    except sqlite3.OperationalError as e:
        # Fallback if we get "no such column" error
        if "no such column: user_id" in str(e):
            print(f"Warning: User ID column missing in topic_progress: {e}")
            # Fallback to non-user-specific update
            database.update_topic_progress(topic_code, topic_title, rating, notes)
        else:
            # Re-raise if it's some other database error
            raise
    
    return jsonify({'success': True})

@app.route('/student/record-exam', methods=['POST'])
@login_required
def student_record_exam():
    """Record exam practice results for the logged-in user."""
    data = request.json
    user_id = session.get('user_id')
    topic_code = data.get('topic_code')
    question_type = data.get('question_type')
    difficulty = data.get('difficulty')
    score = data.get('score')
    max_score = data.get('max_score')
    
    if not all([topic_code, question_type, difficulty, score, max_score]):
        return jsonify({'error': 'Missing required fields'})
    
    database = get_db()
    try:
        # Try to record with user_id
        database.record_exam_practice(topic_code, question_type, difficulty, score, max_score, user_id=user_id)
    except sqlite3.OperationalError as e:
        # Fallback if we get "no such column" error
        if "no such column: user_id" in str(e):
            print(f"Warning: User ID column missing in exam_practice: {e}")
            # Fallback to non-user-specific record
            database.record_exam_practice(topic_code, question_type, difficulty, score, max_score)
        else:
            # Re-raise if it's some other database error
            raise
    
    return jsonify({'success': True})

@app.route('/resources/<path:filename>')
def serve_resource(filename):
    """Serve resource files (PDFs, etc.)."""
    return send_from_directory('resources', filename)

@app.route('/global-chat', methods=['POST'])
@login_required
def global_chat():
    """API endpoint for general CS questions (not tied to a specific topic) for the logged-in user."""
    try:
        data = request.json
        question = data.get('question')
        user_id = session.get('user_id')
        
        if not question:
            return jsonify({'error': 'No question provided'}), 400
        
        # Create a session-specific key for global chat
        global_chat_key = f'global_chat_history_{user_id}'
            
        # Create a session key for global chat if it doesn't exist
        if global_chat_key not in session:
            session[global_chat_key] = []
            
        # Get conversation history from session
        conversation_history = session.get(global_chat_key, [])
        
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
        session[global_chat_key] = conversation_history
        
        return jsonify({'response': response_text})
    except Exception as e:
        print(f"Error in global_chat: {str(e)}")
        return jsonify({'error': f'Error generating response: {str(e)}'}), 500

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port, use_reloader=False)
