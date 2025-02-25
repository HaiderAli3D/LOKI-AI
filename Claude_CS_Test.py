#!/usr/bin/env python3
"""
OCR A-Level Computer Science AI Tutor with File Management

This version includes:
1. Admin interface for managing learning resources and files
2. User interface for students to interact with the AI tutor
3. Behind-the-scenes file processing and knowledge base management
"""

import os
import sys
import json
import time
import anthropic
import sqlite3
import textwrap
import markdown
import traceback
import PyPDF2
import glob
import hashlib
import shutil
from dotenv import load_dotenv
from datetime import datetime
from rich.console import Console
from rich.markdown import Markdown
from rich.syntax import Syntax
from rich.panel import Panel
from rich.table import Table
from rich.progress import Progress, SpinnerColumn, TextColumn

# Define the OCR A-Level CS curriculum structure based on the specification
OCR_CS_CURRICULUM = {
    "computer_systems": {
        "title": "Computer Systems (Component 01)",
        "topics": [
            "1.1 The characteristics of contemporary processors, input, output and storage devices",
            "1.2 Software and software development",
            "1.3 Exchanging data",
            "1.4 Data types, data structures and algorithms",
            "1.5 Legal, moral, cultural and ethical issues"
        ]
    },
    "algorithms_and_programming": {
        "title": "Algorithms and Programming (Component 02)",
        "topics": [
            "2.1 Elements of computational thinking",
            "2.2 Problem solving and programming",
            "2.3 Algorithms"
        ]
    },
    "programming_project": {
        "title": "Programming Project (Component 03/04)",
        "topics": [
            "3.1 Analysis of the problem",
            "3.2 Design of the solution",
            "3.3 Developing the solution",
            "3.4 Evaluation"
        ]
    }
}

# Define detailed subtopics for each main topic in the curriculum
OCR_CS_DETAILED_TOPICS = {
    "1.1": {
        "title": "The characteristics of contemporary processors, input, output and storage devices",
        "subtopics": [
            "1.1.1 Structure and function of the processor",
            "1.1.2 Types of processor",
            "1.1.3 Input, output and storage"
        ]
    },
    "1.2": {
        "title": "Software and software development",
        "subtopics": [
            "1.2.1 Systems Software",
            "1.2.2 Applications Generation",
            "1.2.3 Software Development",
            "1.2.4 Types of Programming Language"
        ]
    },
    "1.3": {
        "title": "Exchanging data",
        "subtopics": [
            "1.3.1 Compression, Encryption and Hashing",
            "1.3.2 Databases",
            "1.3.3 Networks",
            "1.3.4 Web Technologies"
        ]
    },
    "1.4": {
        "title": "Data types, data structures and algorithms",
        "subtopics": [
            "1.4.1 Data Types",
            "1.4.2 Data Structures",
            "1.4.3 Boolean Algebra"
        ]
    },
    "1.5": {
        "title": "Legal, moral, cultural and ethical issues",
        "subtopics": [
            "1.5.1 Computing related legislation",
            "1.5.2 Moral and ethical issues"
        ]
    },
    "2.1": {
        "title": "Elements of computational thinking",
        "subtopics": [
            "2.1.1 Thinking abstractly",
            "2.1.2 Thinking ahead",
            "2.1.3 Thinking procedurally",
            "2.1.4 Thinking logically",
            "2.1.5 Thinking concurrently"
        ]
    },
    "2.2": {
        "title": "Problem solving and programming",
        "subtopics": [
            "2.2.1 Programming techniques",
            "2.2.2 Computational methods"
        ]
    },
    "2.3": {
        "title": "Algorithms",
        "subtopics": [
            "2.3.1 Algorithms for searching, sorting, and pattern recognition"
        ]
    },
    "3.1": {
        "title": "Analysis of the problem (Programming Project)",
        "subtopics": [
            "3.1.1 Problem identification",
            "3.1.2 Stakeholders",
            "3.1.3 Research the problem",
            "3.1.4 Specify the proposed solution"
        ]
    },
    "3.2": {
        "title": "Design of the solution (Programming Project)",
        "subtopics": [
            "3.2.1 Decompose the problem",
            "3.2.2 Describe the solution",
            "3.2.3 Describe the approach to testing"
        ]
    },
    "3.3": {
        "title": "Developing the solution (Programming Project)",
        "subtopics": [
            "3.3.1 Iterative development process",
            "3.3.2 Testing to inform development"
        ]
    },
    "3.4": {
        "title": "Evaluation (Programming Project)",
        "subtopics": [
            "3.4.1 Testing to inform evaluation",
            "3.4.2 Success of the solution",
            "3.4.3 Describe the final product",
            "3.4.4 Maintenance and development"
        ]
    }
}

# Define learning modes
LEARNING_MODES = {
    "explore": "Explore a topic with detailed explanations",
    "practice": "Practice with exam-style questions and problems",
    "code": "Learn through practical coding examples and exercises",
    "review": "Review and consolidate previously covered material",
    "test": "Test your knowledge with assessments based on past papers"
}

class ResourceManager:
    """Manages reference materials and knowledge base for the OCR CS tutor."""
    
    def __init__(self, resource_dir="resources", db_path="knowledge_base.db"):
        self.resource_dir = resource_dir
        self.db_path = db_path
        self.conn = None
        
        # Ensure resource directory exists
        os.makedirs(resource_dir, exist_ok=True)
        
        # Initialize database
        self.init_database()
    
    def init_database(self):
        """Initialize the knowledge base database."""
        try:
            self.conn = sqlite3.connect(self.db_path)
            cursor = self.conn.cursor()
            
            # Create files table
            cursor.execute('''
            CREATE TABLE IF NOT EXISTS files (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                filename TEXT,
                filepath TEXT,
                filetype TEXT,
                file_hash TEXT,
                date_added TIMESTAMP,
                category TEXT,
                metadata TEXT
            )
            ''')
            
            # Create knowledge base table
            cursor.execute('''
            CREATE TABLE IF NOT EXISTS knowledge_base (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                topic_code TEXT,
                content TEXT,
                source_file_id INTEGER,
                metadata TEXT,
                FOREIGN KEY (source_file_id) REFERENCES files (id)
            )
            ''')
            
            self.conn.commit()
        except sqlite3.Error as e:
            print(f"Database error: {e}")
            if self.conn:
                self.conn.close()
            sys.exit(1)
    
    def get_file_hash(self, filepath):
        """Generate hash for a file to check if it's already processed."""
        with open(filepath, 'rb') as f:
            file_hash = hashlib.md5(f.read()).hexdigest()
        return file_hash
    
    def is_file_processed(self, file_hash):
        """Check if a file has already been processed based on its hash."""
        cursor = self.conn.cursor()
        cursor.execute("SELECT id FROM files WHERE file_hash = ?", (file_hash,))
        return cursor.fetchone() is not None
    
    def add_file(self, filepath, category=None):
        """Add a file to the resource database."""
        filename = os.path.basename(filepath)
        filetype = os.path.splitext(filename)[1].lower()[1:]  # Remove the dot
        file_hash = self.get_file_hash(filepath)
        
        # Check if file already exists in database
        if self.is_file_processed(file_hash):
            print(f"File {filename} already processed (based on hash).")
            return None
        
        # Copy file to resource directory
        destination = os.path.join(self.resource_dir, filename)
        shutil.copy2(filepath, destination)
        
        # Add file to database
        cursor = self.conn.cursor()
        cursor.execute(
            "INSERT INTO files (filename, filepath, filetype, file_hash, date_added, category, metadata) VALUES (?, ?, ?, ?, ?, ?, ?)",
            (filename, destination, filetype, file_hash, datetime.now(), category, "{}")
        )
        self.conn.commit()
        
        file_id = cursor.lastrowid
        return file_id
    
    def extract_text_from_pdf(self, pdf_path):
        """Extract text content from a PDF file."""
        text = ""
        try:
            with open(pdf_path, 'rb') as file:
                reader = PyPDF2.PdfReader(file)
                for page in reader.pages:
                    text += page.extract_text() + "\n\n"
        except Exception as e:
            print(f"Error extracting text from PDF: {e}")
        return text
    
    def read_text_file(self, file_path):
        """Read content from a text file."""
        try:
            with open(file_path, 'r', encoding='utf-8') as file:
                return file.read()
        except Exception as e:
            print(f"Error reading text file: {e}")
            return ""
    
    def process_file_content(self, file_id):
        """Process a file and extract content for the knowledge base."""
        cursor = self.conn.cursor()
        cursor.execute("SELECT filepath, filetype FROM files WHERE id = ?", (file_id,))
        result = cursor.fetchone()
        
        if not result:
            return
        
        filepath, filetype = result
        
        # Extract content based on file type
        content = ""
        if filetype == "pdf":
            content = self.extract_text_from_pdf(filepath)
        elif filetype in ["txt", "md", "py", "java", "c", "cpp", "cs"]:
            content = self.read_text_file(filepath)
        else:
            print(f"Unsupported file type: {filetype}")
            return
        
        # Try to automatically categorize content if possible
        topics = self.categorize_content(content)
        
        # Add to knowledge base
        for topic_code in topics:
            cursor.execute(
                "INSERT INTO knowledge_base (topic_code, content, source_file_id, metadata) VALUES (?, ?, ?, ?)",
                (topic_code, content, file_id, "{}")
            )
        
        self.conn.commit()
    
    def categorize_content(self, content):
        """Attempt to categorize content by OCR CS topics."""
        # A simple version - look for topic numbers or keywords
        topics = []
        content_lower = content.lower()
        
        # Check for topic codes (e.g., 1.1.2)
        for main_topic in OCR_CS_DETAILED_TOPICS:
            if main_topic in content or main_topic.replace(".", "") in content:
                topics.append(main_topic)
            
            # Check subtopics
            for subtopic in OCR_CS_DETAILED_TOPICS[main_topic]["subtopics"]:
                subtopic_code = subtopic.split()[0]
                if subtopic_code in content:
                    topics.append(main_topic)
                    break
        
        # If no topics found, add to general knowledge
        if not topics:
            topics = ["general"]
        
        return topics
    
    def bulk_import_from_directory(self, directory_path):
        """Import all supported files from a directory."""
        # Supported file extensions
        supported_extensions = [".pdf", ".txt", ".md", ".py", ".java", ".c", ".cpp", ".cs"]
        
        # Get all files in the directory
        files = []
        for ext in supported_extensions:
            files.extend(glob.glob(os.path.join(directory_path, f"*{ext}")))
        
        print(f"Found {len(files)} supported files in {directory_path}")
        
        # Process each file
        processed_count = 0
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            transient=True,
        ) as progress:
            task = progress.add_task("[green]Processing files...", total=len(files))
            
            for file_path in files:
                progress.update(task, description=f"Processing {os.path.basename(file_path)}")
                file_id = self.add_file(file_path)
                if file_id:
                    self.process_file_content(file_id)
                    processed_count += 1
                progress.advance(task)
        
        return processed_count
    
    def get_knowledge_for_topic(self, topic_code):
        """Retrieve knowledge base content for a specific topic."""
        cursor = self.conn.cursor()
        
        # Get direct matches
        cursor.execute(
            "SELECT content FROM knowledge_base WHERE topic_code = ?",
            (topic_code,)
        )
        results = cursor.fetchall()
        
        # If topic code is like 1.1.2, also get content for parent topic 1.1
        if len(topic_code.split('.')) > 2:
            parent_topic = '.'.join(topic_code.split('.')[:2])
            cursor.execute(
                "SELECT content FROM knowledge_base WHERE topic_code = ?",
                (parent_topic,)
            )
            results.extend(cursor.fetchall())
        
        # Also get general knowledge
        cursor.execute(
            "SELECT content FROM knowledge_base WHERE topic_code = 'general'"
        )
        results.extend(cursor.fetchall())
        
        # Extract content from results
        content = [row[0] for row in results]
        return content
    
    def get_all_file_info(self):
        """Get information about all processed files."""
        cursor = self.conn.cursor()
        cursor.execute(
            "SELECT id, filename, filetype, date_added, category FROM files ORDER BY date_added DESC"
        )
        return cursor.fetchall()
    
    def close(self):
        """Close the database connection."""
        if self.conn:
            self.conn.close()

class OCRCSDatabase:
    """Manages the student's learning progress and history."""
    
    def __init__(self, db_path="ocr_cs_tutor.db"):
        self.db_path = db_path
        self.conn = None
        self.init_database()
        
    def init_database(self):
        """Initialize the database with necessary tables."""
        try:
            self.conn = sqlite3.connect(self.db_path)
            cursor = self.conn.cursor()
            
            # Create session history table
            cursor.execute('''
            CREATE TABLE IF NOT EXISTS sessions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                start_time TIMESTAMP,
                end_time TIMESTAMP,
                topics TEXT,
                summary TEXT
            )
            ''')
            
            # Create topic progress table
            cursor.execute('''
            CREATE TABLE IF NOT EXISTS topic_progress (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                topic_code TEXT,
                topic_title TEXT,
                last_studied TIMESTAMP,
                proficiency INTEGER,
                notes TEXT
            )
            ''')
            
            # Create conversation history table
            cursor.execute('''
            CREATE TABLE IF NOT EXISTS conversation_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id INTEGER,
                timestamp TIMESTAMP,
                role TEXT,
                content TEXT,
                FOREIGN KEY (session_id) REFERENCES sessions (id)
            )
            ''')
            
            # Create exam practice table
            cursor.execute('''
            CREATE TABLE IF NOT EXISTS exam_practice (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                topic_code TEXT,
                question_type TEXT,
                difficulty INTEGER,
                score INTEGER,
                max_score INTEGER,
                date_attempted TIMESTAMP
            )
            ''')
            
            self.conn.commit()
        except sqlite3.Error as e:
            print(f"Database error: {e}")
            if self.conn:
                self.conn.close()
            sys.exit(1)
    
    def start_session(self, topics=None):
        """Start a new learning session."""
        cursor = self.conn.cursor()
        topics_str = json.dumps(topics) if topics else ""
        cursor.execute(
            "INSERT INTO sessions (start_time, topics) VALUES (?, ?)",
            (datetime.now(), topics_str)
        )
        self.conn.commit()
        return cursor.lastrowid
    
    def end_session(self, session_id, summary=None):
        """End a learning session with optional summary."""
        cursor = self.conn.cursor()
        cursor.execute(
            "UPDATE sessions SET end_time = ?, summary = ? WHERE id = ?",
            (datetime.now(), summary, session_id)
        )
        self.conn.commit()
    
    def add_message(self, session_id, role, content):
        """Add a message to the conversation history."""
        cursor = self.conn.cursor()
        cursor.execute(
            "INSERT INTO conversation_history (session_id, timestamp, role, content) VALUES (?, ?, ?, ?)",
            (session_id, datetime.now(), role, content)
        )
        self.conn.commit()
    
    def update_topic_progress(self, topic_code, topic_title, proficiency, notes=None):
        """Update the student's progress on a specific topic."""
        cursor = self.conn.cursor()
        # Check if the topic exists
        cursor.execute(
            "SELECT id FROM topic_progress WHERE topic_code = ?",
            (topic_code,)
        )
        result = cursor.fetchone()
        
        if result:
            # Update existing topic
            cursor.execute(
                "UPDATE topic_progress SET last_studied = ?, proficiency = ?, notes = ? WHERE topic_code = ?",
                (datetime.now(), proficiency, notes, topic_code)
            )
        else:
            # Insert new topic
            cursor.execute(
                "INSERT INTO topic_progress (topic_code, topic_title, last_studied, proficiency, notes) VALUES (?, ?, ?, ?, ?)",
                (topic_code, topic_title, datetime.now(), proficiency, notes)
            )
        self.conn.commit()
    
    def record_exam_practice(self, topic_code, question_type, difficulty, score, max_score):
        """Record results from exam practice attempts."""
        cursor = self.conn.cursor()
        cursor.execute(
            "INSERT INTO exam_practice (topic_code, question_type, difficulty, score, max_score, date_attempted) VALUES (?, ?, ?, ?, ?, ?)",
            (topic_code, question_type, difficulty, score, max_score, datetime.now())
        )
        self.conn.commit()
    
    def get_session_history(self, limit=5):
        """Get recent session history."""
        cursor = self.conn.cursor()
        cursor.execute(
            "SELECT id, start_time, end_time, topics, summary FROM sessions ORDER BY start_time DESC LIMIT ?",
            (limit,)
        )
        return cursor.fetchall()
    
    def get_topic_progress(self):
        """Get the student's progress on all topics."""
        cursor = self.conn.cursor()
        cursor.execute(
            "SELECT topic_code, topic_title, last_studied, proficiency, notes FROM topic_progress ORDER BY topic_code"
        )
        return cursor.fetchall()
    
    def get_exam_progress(self, topic_code=None):
        """Get the student's progress on exam practice questions."""
        cursor = self.conn.cursor()
        if topic_code:
            cursor.execute(
                "SELECT topic_code, question_type, AVG(score*100.0/max_score) as avg_percent FROM exam_practice WHERE topic_code = ? GROUP BY topic_code, question_type",
                (topic_code,)
            )
        else:
            cursor.execute(
                "SELECT topic_code, question_type, AVG(score*100.0/max_score) as avg_percent FROM exam_practice GROUP BY topic_code, question_type"
            )
        return cursor.fetchall()
    
    def get_session_messages(self, session_id):
        """Get all messages from a specific session."""
        cursor = self.conn.cursor()
        cursor.execute(
            "SELECT timestamp, role, content FROM conversation_history WHERE session_id = ? ORDER BY timestamp",
            (session_id,)
        )
        return cursor.fetchall()
    
    def close(self):
        """Close the database connection."""
        if self.conn:
            self.conn.close()

class OCRCSTutor:
    """OCR A-Level Computer Science AI Tutor using Anthropic's Claude API."""
    
    def __init__(self, resource_manager=None):
        self.console = Console()
        self.client = None
        self.db = OCRCSDatabase()
        self.resource_manager = resource_manager
        self.session_id = None
        self.current_topic = None
        self.current_detailed_topic = None
        self.current_mode = None
        self.conversation_history = []
        self.model = "claude-3-7-sonnet-20250219"
        
    def setup_api_client(self):
        """Set up the Anthropic API client."""
        load_dotenv()
        api_key = os.getenv("ANTHROPIC_API_KEY")
        
        if not api_key:
            self.console.print(Panel("API Key Setup", style="bold blue"))
            api_key = input("Please enter your Anthropic API key: ").strip()
            if not api_key:
                self.console.print("[bold red]Error:[/bold red] API key is required to use this tutor.")
                sys.exit(1)
            
            # Ask if they want to save the key for future use
            save_key = input("Would you like to save this key for future use? (y/n): ").strip().lower()
            if save_key == 'y':
                with open(".env", "w") as f:
                    f.write(f"ANTHROPIC_API_KEY={api_key}")
                self.console.print("[green]API key saved to .env file[/green]")
        
        try:
            self.client = anthropic.Anthropic(api_key=api_key)
        except Exception as e:
            self.console.print(f"[bold red]Error setting up API client:[/bold red] {e}")
            sys.exit(1)
    
    def create_system_prompt(self):
        """Create a specialized system prompt for the OCR CS tutor."""
        system_prompt = """
        You are an expert OCR A-Level Computer Science tutor with extensive knowledge of the H446 specification and examination standards. Your purpose is to help students understand complex computer science concepts, practice their skills, and prepare for their examinations.

        TEACHING APPROACH:
        - Start with clear, precise definitions of key concepts
        - Break down complex topics into manageable, logical steps
        - Use analogies and real-world examples to illustrate abstract concepts
        - Provide code examples where relevant, with detailed explanations
        - Check understanding regularly with reflective questions
        - Focus on building both theoretical knowledge and practical skills
        - Summarize key points to reinforce learning
        
        OCR A-LEVEL CURRICULUM AREAS:
        - Computer Systems (Component 01): processors, software development, data exchange, data types/structures, legal/ethical issues
        - Algorithms and Programming (Component 02): computational thinking, problem-solving, programming techniques, standard algorithms
        - Programming Project (Component 03/04): analysis, design, development, testing, evaluation
        
        EXAM PREPARATION:
        - Focus on the specific assessment objectives from the OCR specification
        - Provide exam-style questions and guidance on answering techniques
        - Offer tips on common pitfalls and misconceptions
        - Ensure coverage of all specification points

        RESPONSE FORMAT:
        - Use markdown formatting for clarity
        - For code examples, use proper syntax highlighting
        - Structure explanations logically with clear headings
        - Include diagrams or visual explanations when helpful (using text-based diagrams)
        - End each explanation with summary points and check questions

        Always maintain a supportive, patient tone. Your goal is to build the student's confidence and competence in computer science according to the OCR A-Level specification.
        """
        return textwrap.dedent(system_prompt).strip()
    
    def get_claude_response(self, prompt, include_history=True, include_knowledge=True):
        """Get a response from Claude based on the prompt, conversation history, and knowledge base."""
        try:
            self.console.print("\n[blue]Generating response...[/blue]")
            
            messages = []
            
            # Include conversation history if needed
            if include_history and self.conversation_history:
                messages = self.conversation_history.copy()
            
            # Augment prompt with knowledge base information if available
            augmented_prompt = prompt
            if include_knowledge and self.resource_manager and self.current_detailed_topic:
                topic_code = self.current_detailed_topic.split()[0]
                knowledge = self.resource_manager.get_knowledge_for_topic(topic_code)
                
                if knowledge:
                    # Summarize knowledge to avoid exceeding context limits
                    knowledge_text = "\n\n".join(knowledge)
                    if len(knowledge_text) > 10000:  # Limit knowledge text size
                        knowledge_text = knowledge_text[:10000] + "..."
                    
                    augmented_prompt = f"""
                    [REFERENCE INFORMATION]
                    The following information is from OCR A-Level Computer Science resources related to {self.current_detailed_topic}:
                    
                    {knowledge_text}
                    
                    [END REFERENCE INFORMATION]
                    
                    STUDENT QUESTION:
                    {prompt}
                    
                    Please use the reference information where appropriate to give an accurate, specification-aligned response.
                    """
                    
            # Add the current prompt
            messages.append({"role": "user", "content": augmented_prompt})
            
            # Create a message and get the response
            response = self.client.messages.create(
                model=self.model,
                max_tokens=4096,
                temperature=0.7,
                system=self.create_system_prompt(),
                messages=messages
            )
            
            # Get the response text
            response_text = response.content[0].text
            
            # Update conversation history with the original prompt, not the augmented one
            self.conversation_history.append({"role": "user", "content": prompt})
            self.conversation_history.append({"role": "assistant", "content": response_text})
            
            # Save to database
            if self.session_id:
                self.db.add_message(self.session_id, "user", prompt)
                self.db.add_message(self.session_id, "assistant", response_text)
            
            return response_text
            
        except anthropic.RateLimitError:
            return "I've reached my rate limit. Please wait a moment before trying again."
        except Exception as e:
            self.console.print(f"[bold red]Error:[/bold red] {str(e)}")
            return "Sorry, I couldn't generate a response at this time."
    
    def display_curriculum(self):
        """Display the OCR A-Level CS curriculum structure."""
        table = Table(title="OCR A-Level Computer Science Curriculum (H446)")
        table.add_column("Component", style="cyan")
        table.add_column("Topics", style="green")
        
        for category, info in OCR_CS_CURRICULUM.items():
            topics_text = "\n".join([f"• {topic}" for topic in info["topics"]])
            table.add_row(info["title"], topics_text)
        
        self.console.print(table)
    
    def display_detailed_topics(self, main_topic):
        """Display detailed subtopics for a selected main topic."""
        topic_code = main_topic.split()[0]
        
        if topic_code in OCR_CS_DETAILED_TOPICS:
            table = Table(title=f"Detailed Topics for {OCR_CS_DETAILED_TOPICS[topic_code]['title']}")
            table.add_column("Subtopic", style="cyan")
            
            for subtopic in OCR_CS_DETAILED_TOPICS[topic_code]["subtopics"]:
                table.add_row(subtopic)
            
            self.console.print(table)
        else:
            self.console.print(f"[yellow]No detailed topics found for {main_topic}[/yellow]")
    
    def display_learning_modes(self):
        """Display available learning modes."""
        table = Table(title="Learning Modes")
        table.add_column("Mode", style="cyan")
        table.add_column("Description", style="green")
        
        for mode, description in LEARNING_MODES.items():
            table.add_row(mode, description)
        
        self.console.print(table)
    
    def select_component(self):
        """Allow the user to select a component to study."""
        self.display_curriculum()
        
        self.console.print("\n[bold blue]Select a component:[/bold blue]")
        components = list(OCR_CS_CURRICULUM.keys())
        for i, component in enumerate(components, 1):
            self.console.print(f"{i}. {OCR_CS_CURRICULUM[component]['title']}")
        
        while True:
            try:
                component_choice = int(input("\nEnter component number: "))
                if 1 <= component_choice <= len(components):
                    selected_component = components[component_choice - 1]
                    break
                else:
                    self.console.print("[red]Invalid choice. Please try again.[/red]")
            except ValueError:
                self.console.print("[red]Please enter a number.[/red]")
        
        return selected_component
    
    def select_topic(self, component):
        """Allow the user to select a topic to study within a component."""
        self.console.print(f"\n[bold blue]Topics in {OCR_CS_CURRICULUM[component]['title']}:[/bold blue]")
        topics = OCR_CS_CURRICULUM[component]['topics']
        for i, topic in enumerate(topics, 1):
            self.console.print(f"{i}. {topic}")
        
        while True:
            try:
                topic_choice = int(input("\nEnter topic number: "))
                if 1 <= topic_choice <= len(topics):
                    selected_topic = topics[topic_choice - 1]
                    break
                else:
                    self.console.print("[red]Invalid choice. Please try again.[/red]")
            except ValueError:
                self.console.print("[red]Please enter a number.[/red]")
        
        return selected_topic
    
    def select_detailed_topic(self, main_topic):
        """Allow the user to select a detailed subtopic to study."""
        topic_code = main_topic.split()[0]
        
        if topic_code in OCR_CS_DETAILED_TOPICS:
            self.console.print(f"\n[bold blue]Detailed topics for {OCR_CS_DETAILED_TOPICS[topic_code]['title']}:[/bold blue]")
            subtopics = OCR_CS_DETAILED_TOPICS[topic_code]['subtopics']
            for i, subtopic in enumerate(subtopics, 1):
                self.console.print(f"{i}. {subtopic}")
            
            while True:
                try:
                    subtopic_choice = int(input("\nEnter subtopic number: "))
                    if 1 <= subtopic_choice <= len(subtopics):
                        selected_subtopic = subtopics[subtopic_choice - 1]
                        break
                    else:
                        self.console.print("[red]Invalid choice. Please try again.[/red]")
                except ValueError:
                    self.console.print("[red]Please enter a number.[/red]")
            
            return selected_subtopic
        else:
            self.console.print(f"[yellow]No detailed topics found for {main_topic}. Proceeding with the main topic.[/yellow]")
            return main_topic
    
    def select_learning_mode(self):
        """Allow the user to select a learning mode."""
        self.display_learning_modes()
        
        self.console.print("\n[bold blue]Select a learning mode:[/bold blue]")
        modes = list(LEARNING_MODES.keys())
        for i, mode in enumerate(modes, 1):
            self.console.print(f"{i}. {mode.title()} - {LEARNING_MODES[mode]}")
        
        while True:
            try:
                mode_choice = int(input("\nEnter mode number: "))
                if 1 <= mode_choice <= len(modes):
                    self.current_mode = modes[mode_choice - 1]
                    break
                else:
                    self.console.print("[red]Invalid choice. Please try again.[/red]")
            except ValueError:
                self.console.print("[red]Please enter a number.[/red]")
        
        return self.current_mode
    
    def start_learning_session(self):
        """Start a new learning session."""
        # Select component, topic, and subtopic
        component = self.select_component()
        main_topic = self.select_topic(component)
        detailed_topic = self.select_detailed_topic(main_topic)
        
        # Select learning mode
        mode = self.select_learning_mode()
        
        # Store the current topics
        self.current_topic = main_topic
        self.current_detailed_topic = detailed_topic
        
        # Create session in database
        self.session_id = self.db.start_session([component, main_topic, detailed_topic])
        
        # Reset conversation history
        self.conversation_history = []
        
        # Create initial prompt based on topic and mode
        initial_prompt = self.create_initial_prompt(component, main_topic, detailed_topic, mode)
        
        # Get and display Claude's response
        response = self.get_claude_response(initial_prompt)
        self.display_response(response)
        
        return component, main_topic, detailed_topic, mode
    
    def create_initial_prompt(self, component, main_topic, detailed_topic, mode):
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
    
    def display_response(self, response):
        """Display Claude's response with rich formatting."""
        try:
            # Parse markdown in the response
            md = Markdown(response)
            self.console.print(Panel(md, border_style="blue", title="Claude's Response", title_align="left"))
        except Exception:
            # Fallback to plain text if markdown parsing fails
            self.console.print(Panel(response, border_style="blue", title="Claude's Response", title_align="left"))
    
    def display_progress(self):
        """Display the student's learning progress across the OCR A-Level specification."""
        progress_data = self.db.get_topic_progress()
        
        if not progress_data:
            self.console.print("[yellow]No progress data available yet.[/yellow]")
            return
        
        table = Table(title="Your OCR A-Level Computer Science Progress")
        table.add_column("Topic", style="cyan")
        table.add_column("Last Studied", style="yellow")
        table.add_column("Proficiency", style="red")
        table.add_column("Notes", style="green")
        
        for row in progress_data:
            topic_code, topic_title, last_studied, proficiency, notes = row
            proficiency_display = "★" * proficiency + "☆" * (5 - proficiency)
            date_display = datetime.fromisoformat(last_studied).strftime("%Y-%m-%d %H:%M")
            notes_display = notes if notes else ""
            table.add_row(f"{topic_code}: {topic_title}", date_display, proficiency_display, notes_display)
        
        self.console.print(table)
    
    def display_exam_progress(self):
        """Display the student's progress on exam-style questions."""
        exam_data = self.db.get_exam_progress()
        
        if not exam_data:
            self.console.print("[yellow]No exam practice data available yet.[/yellow]")
            return
        
        table = Table(title="Your Exam Practice Progress")
        table.add_column("Topic", style="cyan")
        table.add_column("Question Type", style="yellow")
        table.add_column("Average Score", style="red")
        
        for row in exam_data:
            topic_code, question_type, avg_percent = row
            score_display = f"{avg_percent:.1f}%"
            table.add_row(topic_code, question_type, score_display)
        
        self.console.print(table)
    
    def rate_understanding(self):
        """Allow the student to rate their understanding of the current topic."""
        if not self.current_topic:
            return
        
        self.console.print("\n[bold blue]Rate your understanding of this topic:[/bold blue]")
        self.console.print("1: Very poor understanding")
        self.console.print("2: Poor understanding")
        self.console.print("3: Moderate understanding")
        self.console.print("4: Good understanding")
        self.console.print("5: Excellent understanding")
        
        while True:
            try:
                rating = int(input("\nYour rating (1-5): "))
                if 1 <= rating <= 5:
                    notes = input("Any notes you'd like to add about this topic? (optional): ")
                    
                    # Extract topic code from current_detailed_topic
                    topic_code = self.current_detailed_topic.split()[0] if self.current_detailed_topic else self.current_topic.split()[0]
                    
                    self.db.update_topic_progress(
                        topic_code, 
                        self.current_detailed_topic or self.current_topic, 
                        rating, 
                        notes
                    )
                    self.console.print("[green]Progress updated![/green]")
                    break
                else:
                    self.console.print("[red]Invalid rating. Please enter a number between 1 and 5.[/red]")
            except ValueError:
                self.console.print("[red]Please enter a number.[/red]")
    
    def record_exam_score(self):
        """Allow the student to record a score from an exam practice session."""
        if not self.current_topic:
            return
        
        self.console.print("\n[bold blue]Record your exam practice score:[/bold blue]")
        
        # Extract topic code from current_detailed_topic
        topic_code = self.current_detailed_topic.split()[0] if self.current_detailed_topic else self.current_topic.split()[0]
        
        question_type = input("Question type (e.g., short answer, extended response): ")
        
        while True:
            try:
                difficulty = int(input("Difficulty level (1-3): "))
                if 1 <= difficulty <= 3:
                    break
                else:
                    self.console.print("[red]Invalid difficulty. Please enter a number between 1 and 3.[/red]")
            except ValueError:
                self.console.print("[red]Please enter a number.[/red]")
        
        while True:
            try:
                score = int(input("Your score: "))
                max_score = int(input("Maximum possible score: "))
                if 0 <= score <= max_score:
                    self.db.record_exam_practice(topic_code, question_type, difficulty, score, max_score)
                    self.console.print("[green]Exam practice score recorded![/green]")
                    break
                else:
                    self.console.print("[red]Invalid score. Your score must be between 0 and the maximum score.[/red]")
            except ValueError:
                self.console.print("[red]Please enter numeric values.[/red]")
    
    def interactive_mode(self):
        """Run the interactive OCR A-Level Computer Science tutor session."""
        try:
            self.console.print(Panel.fit(
                "[bold green]OCR A-Level Computer Science AI Tutor (H446)[/bold green]\n\n"
                "An interactive learning tool powered by Claude AI to help you master "
                "the OCR A-Level Computer Science specification and prepare for your exams.",
                title="Welcome", title_align="center", border_style="green"
            ))
            
            # Start a learning session
            component, main_topic, detailed_topic, mode = self.start_learning_session()
            
            # Main interaction loop
            while True:
                # Get user input
                user_input = input("\n📝 [Enter your question, 'commands' for options, or 'exit' to quit]: ")
                
                # Check for special commands
                if user_input.lower() == 'exit':
                    break
                elif user_input.lower() == 'commands':
                    self.display_commands()
                    continue
                elif user_input.lower() == 'component':
                    component = self.select_component()
                    main_topic = self.select_topic(component)
                    detailed_topic = self.select_detailed_topic(main_topic)
                    self.current_topic = main_topic
                    self.current_detailed_topic = detailed_topic
                    
                    initial_prompt = self.create_initial_prompt(component, main_topic, detailed_topic, self.current_mode)
                    response = self.get_claude_response(initial_prompt, include_history=False)
                    self.display_response(response)
                    continue
                elif user_input.lower() == 'topic':
                    main_topic = self.select_topic(component)
                    detailed_topic = self.select_detailed_topic(main_topic)
                    self.current_topic = main_topic
                    self.current_detailed_topic = detailed_topic
                    
                    initial_prompt = self.create_initial_prompt(component, main_topic, detailed_topic, self.current_mode)
                    response = self.get_claude_response(initial_prompt, include_history=False)
                    self.display_response(response)
                    continue
                elif user_input.lower() == 'mode':
                    mode = self.select_learning_mode()
                    initial_prompt = self.create_initial_prompt(component, main_topic, detailed_topic, mode)
                    response = self.get_claude_response(initial_prompt, include_history=False)
                    self.display_response(response)
                    continue
                elif user_input.lower() == 'progress':
                    self.display_progress()
                    continue
                elif user_input.lower() == 'exam':
                    self.display_exam_progress()
                    continue
                elif user_input.lower() == 'rate':
                    self.rate_understanding()
                    continue
                elif user_input.lower() == 'score':
                    self.record_exam_score()
                    continue
                elif user_input.lower() == 'clear':
                    self.conversation_history = []
                    self.console.print("[green]Conversation history cleared.[/green]")
                    continue
                elif user_input.lower() == 'summary':
                    summary_prompt = f"Please provide a concise summary of the key points about {self.current_detailed_topic or self.current_topic} for revision purposes, highlighting the most important information for the OCR A-Level exam."
                    response = self.get_claude_response(summary_prompt)
                    self.display_response(response)
                    continue
                elif user_input.lower() == 'specification':
                    spec_prompt = f"Please explain exactly what the OCR A-Level Computer Science specification (H446) requires students to know about {self.current_detailed_topic or self.current_topic}, listing all the specific points that could be examined."
                    response = self.get_claude_response(spec_prompt)
                    self.display_response(response)
                    continue
                elif user_input.lower() == 'exam-tips':
                    tips_prompt = f"Please provide specific exam tips for answering questions on {self.current_detailed_topic or self.current_topic} in the OCR A-Level Computer Science exam. Include advice on common pitfalls, mark scheme requirements, and how to structure answers effectively."
                    response = self.get_claude_response(tips_prompt)
                    self.display_response(response)
                    continue
                
                # Get and display Claude's response
                response = self.get_claude_response(user_input)
                self.display_response(response)
        
        except KeyboardInterrupt:
            self.console.print("\n\n[yellow]Session interrupted by user.[/yellow]")
        except Exception as e:
            self.console.print(f"\n[bold red]Error:[/bold red] {str(e)}")
            traceback.print_exc()
        finally:
            # End the session and save progress
            if self.session_id:
                summary_prompt = "Please provide a brief summary of what we covered in this session, focusing on the key concepts and learning points."
                try:
                    summary = self.get_claude_response(summary_prompt)
                    self.db.end_session(self.session_id, summary)
                except:
                    self.db.end_session(self.session_id)
                    
            self.console.print("\n[bold green]Thank you for using the OCR A-Level Computer Science AI Tutor![/bold green]")
            self.console.print("Your progress has been saved.")
            self.db.close()
    
    def display_commands(self):
        """Display available commands."""
        commands = [
            ("exit", "Exit the tutor"),
            ("commands", "Display this list of commands"),
            ("component", "Change to a different component of the specification"),
            ("topic", "Change the current topic"),
            ("mode", "Change the learning mode"),
            ("progress", "View your overall learning progress"),
            ("exam", "View your exam practice progress"),
            ("rate", "Rate your understanding of the current topic"),
            ("score", "Record a score from exam practice"),
            ("clear", "Clear the conversation history"),
            ("summary", "Get a revision summary of the current topic"),
            ("specification", "See exactly what the specification requires for this topic"),
            ("exam-tips", "Get exam-specific tips for this topic")
        ]
        
        table = Table(title="Available Commands")
        table.add_column("Command", style="cyan")
        table.add_column("Description", style="green")
        
        for command, description in commands:
            table.add_row(command, description)
        
        self.console.print(table)

class OCRCSAdmin:
    """Admin interface for managing OCR A-Level Computer Science resources."""
    
    def __init__(self):
        self.console = Console()
        self.resource_manager = ResourceManager()
    
    def run(self):
        """Run the admin interface."""
        try:
            self.console.print(Panel.fit(
                "[bold green]OCR A-Level Computer Science Resource Manager[/bold green]\n\n"
                "Admin interface for managing resources and knowledge base for the AI tutor.",
                title="Admin Interface", title_align="center", border_style="green"
            ))
            
            while True:
                self.display_menu()
                choice = input("\nEnter your choice: ").strip()
                
                if choice == '1':
                    self.import_directory()
                elif choice == '2':
                    self.import_file()
                elif choice == '3':
                    self.view_resources()
                elif choice == '4':
                    self.view_knowledge_base()
                elif choice == '5':
                    print("Starting user tutor interface...")
                    # Initialize and start the user tutor
                    tutor = OCRCSTutor(resource_manager=self.resource_manager)
                    tutor.setup_api_client()
                    tutor.interactive_mode()
                elif choice == '0':
                    self.console.print("[green]Exiting admin interface.[/green]")
                    break
                else:
                    self.console.print("[red]Invalid choice. Please try again.[/red]")
        
        except KeyboardInterrupt:
            self.console.print("\n\n[yellow]Admin session interrupted.[/yellow]")
        except Exception as e:
            self.console.print(f"\n[bold red]Error:[/bold red] {str(e)}")
            traceback.print_exc()
        finally:
            # Clean up resources
            self.resource_manager.close()
    
    def display_menu(self):
        """Display the admin menu."""
        self.console.print("\n[bold blue]Admin Menu:[/bold blue]")
        self.console.print("1. Import resources from directory")
        self.console.print("2. Import single file")
        self.console.print("3. View imported resources")
        self.console.print("4. View knowledge base")
        self.console.print("5. Start user tutor interface")
        self.console.print("0. Exit")
    
    def import_directory(self):
        """Import resources from a directory."""
        directory_path = input("\nEnter directory path to import: ").strip()
        
        if not os.path.isdir(directory_path):
            self.console.print(f"[red]Error: {directory_path} is not a valid directory.[/red]")
            return
        
        count = self.resource_manager.bulk_import_from_directory(directory_path)
        self.console.print(f"[green]Successfully processed {count} files from {directory_path}.[/green]")
    
    def import_file(self):
        """Import a single file."""
        file_path = input("\nEnter file path to import: ").strip()
        
        if not os.path.isfile(file_path):
            self.console.print(f"[red]Error: {file_path} is not a valid file.[/red]")
            return
        
        category = input("Enter category (optional): ").strip() or None
        
        file_id = self.resource_manager.add_file(file_path, category)
        if file_id:
            self.resource_manager.process_file_content(file_id)
            self.console.print(f"[green]Successfully processed {os.path.basename(file_path)}.[/green]")
        else:
            self.console.print(f"[yellow]File {os.path.basename(file_path)} was not processed (may already exist).[/yellow]")
    
    def view_resources(self):
        """View all imported resources."""
        files = self.resource_manager.get_all_file_info()
        
        if not files:
            self.console.print("[yellow]No resources have been imported yet.[/yellow]")
            return
        
        table = Table(title="Imported Resources")
        table.add_column("ID", style="cyan")
        table.add_column("Filename", style="green")
        table.add_column("Type", style="yellow")
        table.add_column("Date Added", style="blue")
        table.add_column("Category", style="magenta")
        
        for file_id, filename, filetype, date_added, category in files:
            date_display = datetime.fromisoformat(date_added).strftime("%Y-%m-%d %H:%M")
            category_display = category or "N/A"
            table.add_row(str(file_id), filename, filetype, date_display, category_display)
        
        self.console.print(table)
    
    def view_knowledge_base(self):
        """View knowledge base content by topic."""
        self.console.print("\n[bold blue]Available Topics:[/bold blue]")
        
        # Display all topics for selection
        topics = []
        for category in OCR_CS_CURRICULUM:
            for topic in OCR_CS_CURRICULUM[category]['topics']:
                topic_code = topic.split()[0]
                topics.append((topic_code, topic))
                
                # Also add detailed subtopics if available
                if topic_code in OCR_CS_DETAILED_TOPICS:
                    for subtopic in OCR_CS_DETAILED_TOPICS[topic_code]['subtopics']:
                        subtopic_code = subtopic.split()[0]
                        topics.append((subtopic_code, subtopic))
        
        # Sort by topic code
        topics.sort(key=lambda x: x[0])
        
        # Display topics
        for i, (code, description) in enumerate(topics, 1):
            self.console.print(f"{i}. {code}: {description}")
        
        # Get topic selection
        try:
            choice = int(input("\nEnter topic number (0 to cancel): "))
            if choice == 0:
                return
            
            if 1 <= choice <= len(topics):
                topic_code, topic_description = topics[choice - 1]
                
                # Get knowledge for the selected topic
                knowledge = self.resource_manager.get_knowledge_for_topic(topic_code)
                
                if not knowledge:
                    self.console.print(f"[yellow]No knowledge base content found for {topic_description}.[/yellow]")
                    return
                
                # Display knowledge content
                self.console.print(f"\n[bold blue]Knowledge base content for {topic_description}:[/bold blue]")
                
                for i, content in enumerate(knowledge, 1):
                    # Truncate content for display
                    display_content = content[:500] + "..." if len(content) > 500 else content
                    self.console.print(Panel(display_content, title=f"Content {i}", border_style="blue"))
            else:
                self.console.print("[red]Invalid topic number.[/red]")
        except ValueError:
            self.console.print("[red]Please enter a number.[/red]")

def main():
    """Main function to run either the admin or user interface."""
    console = Console()
    
    # Check if admin mode is requested
    if len(sys.argv) > 1 and sys.argv[1] == "--admin":
        # Run admin interface
        admin = OCRCSAdmin()
        admin.run()
    else:
        # Run user interface with resource manager if available
        try:
            resource_manager = ResourceManager()
            
            # Run the interactive tutor
            tutor = OCRCSTutor(resource_manager=resource_manager)
            tutor.setup_api_client()
            tutor.interactive_mode()
            
            # Clean up resources
            resource_manager.close()
        except Exception as e:
            console.print(f"\n[bold red]Fatal error:[/bold red] {str(e)}")
            traceback.print_exc()
            sys.exit(1)

if __name__ == "__main__":
    main()