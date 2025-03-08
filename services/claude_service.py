"""
Claude service for OCR A-Level Computer Science AI Tutor
"""
import os
import json
import anthropic
from flask import current_app, g
from models.message import Message
from models.session import Session
from models.knowledge_base import KnowledgeBase

class ClaudeService:
    """Claude service class"""
    
    @staticmethod
    def get_client():
        """Get Anthropic client"""
        if 'anthropic_client' not in g:
            api_key = os.environ.get('ANTHROPIC_API_KEY')
            g.anthropic_client = anthropic.Anthropic(api_key=api_key)
        return g.anthropic_client
    
    @staticmethod
    def get_model():
        """Get Claude model"""
        return os.environ.get('ANTHROPIC_MODEL', 'claude-3-5-haiku-20241022')
    
    @staticmethod
    def get_system_prompt(topic_id=None, mode=None):
        """Get system prompt based on topic and mode"""
        # Base system prompt
        system_prompt = """You are an AI tutor for OCR A-Level Computer Science students.
Your goal is to help students understand computer science concepts, practice their skills, and prepare for their exams.
You should be helpful, educational, and encouraging. Provide clear explanations and examples.
When appropriate, use code examples to illustrate concepts.
"""
        
        # Add topic-specific context if available
        if topic_id:
            topic_context = KnowledgeBase.get_context_for_topic(topic_id)
            if topic_context:
                system_prompt += f"\n\nHere is information about the topic '{topic_id}':\n\n{topic_context}"
        
        # Add mode-specific instructions
        if mode:
            if mode == 'explore':
                system_prompt += """
                
In EXPLORE mode, your goal is to help the student understand the topic. Provide clear explanations, examples, and analogies.
Break down complex concepts into simpler parts. Use diagrams or code examples when appropriate.
Ask questions to check understanding and encourage the student to think critically.
"""
            elif mode == 'practice':
                system_prompt += """
                
In PRACTICE mode, your goal is to help the student practice their skills. Provide practice questions and problems.
Give feedback on the student's answers and help them understand their mistakes.
Gradually increase the difficulty of the questions as the student demonstrates understanding.
"""
            elif mode == 'code':
                system_prompt += """
                
In CODE mode, your goal is to help the student practice programming. Provide coding challenges and problems.
Give feedback on the student's code and help them understand their mistakes.
Explain programming concepts and best practices. Provide example code when appropriate.
"""
            elif mode == 'review':
                system_prompt += """
                
In REVIEW mode, your goal is to help the student review what they've learned. Summarize key concepts and ideas.
Highlight important points and common misconceptions. Connect different concepts and show how they relate.
Ask questions to check understanding and identify areas that need more work.
"""
            elif mode == 'test':
                system_prompt += """
                
In TEST mode, your goal is to simulate an exam experience. Provide exam-style questions and problems.
Do not give hints or feedback until the student has submitted their answer.
After the student submits their answer, provide detailed feedback and a model answer.
"""
        
        return system_prompt
    
    @staticmethod
    def create_message(session_id, role, content):
        """Create a message in a session"""
        message = Message(session_id=session_id, role=role, content=content)
        from config.database_config import db
        db.session.add(message)
        db.session.commit()
        return message
    
    @staticmethod
    def get_conversation_history(session_id):
        """Get conversation history for a session"""
        return Message.get_anthropic_messages(session_id)
    
    @staticmethod
    def send_message(session_id, content):
        """Send a message to Claude and get a response"""
        # Get client and model
        client = ClaudeService.get_client()
        model = ClaudeService.get_model()
        
        # Get session
        session = Session.query.get(session_id)
        if not session:
            current_app.logger.error(f"Session not found: {session_id}")
            return None
        
        # Create user message
        ClaudeService.create_message(session_id, 'user', content)
        
        # Get conversation history
        messages = ClaudeService.get_conversation_history(session_id)
        
        # Get system prompt
        system_prompt = ClaudeService.get_system_prompt(session.topic_id, session.mode)
        
        try:
            # Send message to Claude
            response = client.messages.create(
                model=model,
                system=system_prompt,
                messages=messages,
                max_tokens=4096
            )
            
            # Extract response content
            response_content = response.content[0].text
            
            # Create assistant message
            assistant_message = ClaudeService.create_message(session_id, 'assistant', response_content)
            
            return {
                'id': assistant_message.id,
                'content': response_content,
                'role': 'assistant',
                'timestamp': assistant_message.timestamp.isoformat()
            }
            
        except Exception as e:
            current_app.logger.error(f"Error sending message to Claude: {e}")
            return None
    
    @staticmethod
    def generate_exam_questions(topic_id, count=5):
        """Generate exam questions for a topic"""
        # Get client and model
        client = ClaudeService.get_client()
        model = ClaudeService.get_model()
        
        # Get topic context
        topic_context = KnowledgeBase.get_context_for_topic(topic_id)
        
        # Create system prompt
        system_prompt = f"""You are an AI tutor for OCR A-Level Computer Science students.
Your task is to generate {count} exam-style questions for the topic '{topic_id}'.
Each question should be challenging but fair, and should test the student's understanding of the topic.
Include a mix of question types, such as multiple choice, short answer, and longer essay-style questions.
For each question, provide a model answer and marking scheme.

Format the output as a JSON array of question objects, each with the following structure:
{{
  "question": "The question text",
  "type": "multiple_choice|short_answer|essay",
  "options": ["Option A", "Option B", "Option C", "Option D"] (for multiple choice questions only),
  "answer": "The model answer",
  "marks": 5 (the number of marks for the question)
}}
"""
        
        if topic_context:
            system_prompt += f"\n\nHere is information about the topic '{topic_id}':\n\n{topic_context}"
        
        try:
            # Send message to Claude
            response = client.messages.create(
                model=model,
                system=system_prompt,
                messages=[
                    {"role": "user", "content": f"Generate {count} exam questions for the topic '{topic_id}'."}
                ],
                max_tokens=4096
            )
            
            # Extract response content
            response_content = response.content[0].text
            
            # Parse JSON from response
            # Find JSON in response (it might be wrapped in markdown code blocks)
            json_start = response_content.find('[')
            json_end = response_content.rfind(']') + 1
            
            if json_start >= 0 and json_end > json_start:
                json_str = response_content[json_start:json_end]
                questions = json.loads(json_str)
                return questions
            
            # If JSON parsing fails, return the raw response
            current_app.logger.warning(f"Failed to parse JSON from Claude response: {response_content}")
            return response_content
            
        except Exception as e:
            current_app.logger.error(f"Error generating exam questions: {e}")
            return None
    
    @staticmethod
    def evaluate_exam_answer(question, student_answer):
        """Evaluate a student's answer to an exam question"""
        # Get client and model
        client = ClaudeService.get_client()
        model = ClaudeService.get_model()
        
        # Create system prompt
        system_prompt = """You are an AI tutor for OCR A-Level Computer Science students.
Your task is to evaluate a student's answer to an exam question.
Provide detailed feedback on the answer, including what was good and what could be improved.
Assign a score based on the marking scheme provided.

Format the output as a JSON object with the following structure:
{
  "score": 5 (the score assigned to the answer),
  "max_score": 10 (the maximum possible score),
  "feedback": "Detailed feedback on the answer",
  "model_answer": "A model answer for comparison"
}
"""
        
        try:
            # Send message to Claude
            response = client.messages.create(
                model=model,
                system=system_prompt,
                messages=[
                    {
                        "role": "user", 
                        "content": f"""
Question: {question['question']}
Marks: {question['marks']}
Model Answer: {question['answer']}

Student Answer: {student_answer}

Please evaluate the student's answer.
"""
                    }
                ],
                max_tokens=2048
            )
            
            # Extract response content
            response_content = response.content[0].text
            
            # Parse JSON from response
            # Find JSON in response (it might be wrapped in markdown code blocks)
            json_start = response_content.find('{')
            json_end = response_content.rfind('}') + 1
            
            if json_start >= 0 and json_end > json_start:
                json_str = response_content[json_start:json_end]
                evaluation = json.loads(json_str)
                return evaluation
            
            # If JSON parsing fails, return the raw response
            current_app.logger.warning(f"Failed to parse JSON from Claude response: {response_content}")
            return response_content
            
        except Exception as e:
            current_app.logger.error(f"Error evaluating exam answer: {e}")
            return None
