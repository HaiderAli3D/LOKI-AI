// OCR A-Level Computer Science AI Tutor - Chat Interface

// Elements
const chatMessages = document.getElementById('chat-messages');
const userInput = document.getElementById('user-input');
const sendButton = document.getElementById('send-btn');
const modeBtns = document.querySelectorAll('.mode-btn');
const rateBtn = document.getElementById('rate-understanding-btn');
const examBtn = document.getElementById('record-exam-btn');
const rateModal = document.getElementById('rate-modal');
const examModal = document.getElementById('exam-modal');
const closeBtns = document.querySelectorAll('.close-modal');
const rateForm = document.getElementById('rate-form');
const examForm = document.getElementById('exam-form');

// Initialize with welcome message
window.addEventListener('DOMContentLoaded', () => {
    // Get initial response based on topic and mode
    sendInitialPrompt();
});

// Mode selection
modeBtns.forEach(btn => {
    btn.addEventListener('click', () => {
        // Update active button
        modeBtns.forEach(b => b.classList.remove('active'));
        btn.classList.add('active');
        
        // Update current mode
        currentMode = btn.dataset.mode;
        
        // Send initial prompt for the new mode
        sendInitialPrompt();
    });
});

// Send message
sendButton.addEventListener('click', sendMessage);
userInput.addEventListener('keydown', e => {
    if (e.key === 'Enter' && !e.shiftKey) {
        e.preventDefault();
        sendMessage();
    }
});

// Track conversation history
let conversationHistory = [];

// Modal controls
rateBtn.addEventListener('click', () => {
    rateModal.style.display = 'block';
});

examBtn.addEventListener('click', () => {
    examModal.style.display = 'block';
});

closeBtns.forEach(btn => {
    btn.addEventListener('click', () => {
        rateModal.style.display = 'none';
        examModal.style.display = 'none';
    });
});

window.addEventListener('click', e => {
    if (e.target === rateModal) {
        rateModal.style.display = 'none';
    }
    if (e.target === examModal) {
        examModal.style.display = 'none';
    }
});

// Form submissions
rateForm.addEventListener('submit', e => {
    e.preventDefault();
    
    const formData = new FormData(rateForm);
    const rating = formData.get('rating');
    const notes = formData.get('notes');
    
    if (!rating) {
        alert('Please select a rating');
        return;
    }
    
    // Send rating to server
    fetch('/student/rate-topic', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({
            topic_code: topicCode,
            topic_title: topicTitle,
            rating: parseInt(rating),
            notes: notes
        })
    })
    .then(response => response.json())
    .then(data => {
        if (data.error) {
            alert('Error: ' + data.error);
        } else {
            // Close modal and reset form
            rateModal.style.display = 'none';
            rateForm.reset();
            
            // Add system message
            addMessage('system', 'Your understanding rating has been saved.');
        }
    })
    .catch(error => {
        console.error('Error:', error);
        alert('Error saving rating. Please try again.');
    });
});

examForm.addEventListener('submit', e => {
    e.preventDefault();
    
    const questionType = document.getElementById('question-type').value;
    const difficulty = document.getElementById('difficulty').value;
    const score = document.getElementById('score').value;
    const maxScore = document.getElementById('max-score').value;
    
    if (parseInt(score) > parseInt(maxScore)) {
        alert('Score cannot be greater than maximum score');
        return;
    }
    
    // Send exam score to server
    fetch('/student/record-exam', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({
            topic_code: topicCode,
            question_type: questionType,
            difficulty: parseInt(difficulty),
            score: parseInt(score),
            max_score: parseInt(maxScore)
        })
    })
    .then(response => response.json())
    .then(data => {
        if (data.error) {
            alert('Error: ' + data.error);
        } else {
            // Close modal and reset form
            examModal.style.display = 'none';
            examForm.reset();
            
            // Add system message
            addMessage('system', 'Your exam practice score has been recorded.');
        }
    })
    .catch(error => {
        console.error('Error:', error);
        alert('Error recording score. Please try again.');
    });
});

// Pre-written responses for different topics and modes
const preWrittenResponses = {
    // Default response if no specific match is found
    "default": {
        "explore": "# OCR A-Level Computer Science\n\nWelcome to this topic! This section covers key concepts that are essential for your A-Level Computer Science curriculum.\n\n## Key Points\n\n- Computer Science involves the study of computation, information, and automation\n- Understanding both theoretical and practical aspects is important\n- This topic connects to many other areas in the specification\n\n## Learning Objectives\n\n- Understand the fundamental concepts of this topic\n- Apply these concepts to solve problems\n- Relate this knowledge to other areas of computer science\n\nLet me know if you have any specific questions about this topic!",
        "practice": "# Practice Questions\n\n## Basic Knowledge\n\n1. What are the main components of a computer system?\n2. Explain the difference between hardware and software.\n\n## Application (Medium Difficulty)\n\n3. How does the fetch-execute cycle work in a processor?\n4. Compare and contrast different types of storage devices.\n\n## Analysis/Evaluation (Higher Level)\n\n5. Evaluate the impact of quantum computing on current encryption methods.\n6. Analyze the ethical implications of artificial intelligence in modern society.\n\nTry answering these questions to test your understanding of the topic.",
        "code": "# Coding Examples\n\n## Basic Example\n```python\n# Simple function to demonstrate a concept\ndef example_function(parameter):\n    result = parameter * 2\n    return result\n\n# Test the function\nprint(example_function(5))  # Output: 10\n```\n\n## How It Works\n- The function takes a parameter\n- It multiplies the parameter by 2\n- It returns the result\n\nTry modifying this code to perform different operations!",
        "review": "# Topic Review Summary\n\n## Key Definitions\n- **Term 1**: Definition of first important concept\n- **Term 2**: Definition of second important concept\n- **Term 3**: Definition of third important concept\n\n## Important Concepts\n1. First major concept in this topic\n2. Second major concept in this topic\n3. Third major concept in this topic\n\n## Connections to Other Topics\n- How this relates to hardware components\n- How this relates to software development\n- How this relates to data structures\n\n## Quick Recall Questions\n1. What is the purpose of this component?\n2. How does this process work?\n3. Why is this concept important?",
        "test": "# Mini-Assessment\n\n## Question 1 (3 marks)\nExplain the term 'abstraction' in computing.\n\n## Question 2 (4 marks)\nDescribe the fetch-execute cycle with reference to the registers involved.\n\n## Question 3 (6 marks)\nCompare and contrast high-level and low-level programming languages.\n\n## Question 4 (8 marks)\nEvaluate the benefits and drawbacks of different storage technologies for a school computer system.\n\n## Question 5 (9 marks)\nDiscuss the ethical, legal, and cultural implications of artificial intelligence in healthcare.\n\n**Total: 30 marks**\n**Grade Boundaries:**\nA: 24+ | B: 21+ | C: 18+ | D: 15+ | E: 12+"
    },
    // Specific responses for particular topics can be added here
    "1.1.1": {
        "explore": "# Structure and Function of the Processor\n\nThe processor (CPU) is the brain of the computer system, responsible for executing instructions and performing calculations.\n\n## Key Components\n\n- **Control Unit (CU)**: Manages the execution of instructions\n- **Arithmetic Logic Unit (ALU)**: Performs mathematical and logical operations\n- **Registers**: Small, fast memory locations within the CPU\n- **Cache**: High-speed memory that stores frequently accessed data\n\n## The Fetch-Execute Cycle\n\n1. **Fetch**: Retrieve instruction from memory\n2. **Decode**: Interpret what the instruction means\n3. **Execute**: Perform the operation\n4. **Store**: Save the result\n\nThis cycle forms the foundation of how all programs run on a computer system.",
        "practice": "# Practice Questions on Processor Structure\n\n## Basic Knowledge\n\n1. Name the four main components of the CPU.\n2. What is the purpose of the Program Counter (PC) register?\n\n## Application (Medium Difficulty)\n\n3. Explain how the fetch-decode-execute cycle works with reference to specific registers.\n4. How does cache memory improve processor performance?\n\n## Analysis/Evaluation (Higher Level)\n\n5. Evaluate how different processor architectures affect performance for specific tasks.\n6. Analyze the relationship between clock speed, cores, and overall processor performance.\n\nTry answering these questions to test your understanding of processor structure and function."
    },
    "2.1.1": {
        "explore": "# Thinking Abstractly\n\nAbstraction is a fundamental concept in computer science that involves simplifying complex systems by modeling relevant aspects while ignoring irrelevant details.\n\n## Key Principles\n\n- **Removing unnecessary detail**: Focus only on what's important for the current problem\n- **Creating models**: Represent systems in a simplified way\n- **Identifying patterns**: Recognize similarities across different problems\n- **Generalization**: Apply solutions to a wider range of problems\n\n## Levels of Abstraction in Computing\n\n1. **Hardware level**: Physical components and electronic signals\n2. **Assembly language level**: Basic machine instructions\n3. **High-level language**: Human-readable programming code\n4. **Application level**: User interfaces and functionality\n\nAbstraction allows us to manage complexity and solve problems more effectively."
    }
};

function sendInitialPrompt() {
    // Clear chat
    chatMessages.innerHTML = '';
    
    // Add loading message
    addMessage('system', 'Loading...');
    
    // Reset conversation history
    conversationHistory = [];
    
    // Short timeout to simulate loading
    setTimeout(() => {
        // Remove loading message
        chatMessages.innerHTML = '';
        
        // Get pre-written response based on topic and mode
        let response;
        
        // Try to find a specific response for this topic and mode
        if (preWrittenResponses[topicCode] && preWrittenResponses[topicCode][currentMode]) {
            response = preWrittenResponses[topicCode][currentMode];
        } 
        // Try to find a response for just this topic with default mode
        else if (preWrittenResponses[topicCode] && preWrittenResponses[topicCode]["explore"]) {
            response = preWrittenResponses[topicCode]["explore"];
        }
        // Use default response for this mode
        else {
            response = preWrittenResponses["default"][currentMode] || preWrittenResponses["default"]["explore"];
        }
        
        // Add response
        addMessage('assistant', response);
        
        // Update conversation history
        conversationHistory.push({
            role: "assistant",
            content: response
        });
        
    }, 500); // 500ms delay to simulate loading
}

// Pre-written responses for user questions
const userQuestionResponses = {
    "default": "I understand your question. This topic involves several key concepts that are important for your A-Level Computer Science curriculum.\n\nThe main points to remember are:\n\n1. Understanding the fundamental principles\n2. Applying these concepts to practical scenarios\n3. Recognizing how this connects to other areas of computer science\n\nFor more specific information, try asking about particular aspects of this topic or check the OCR specification for detailed requirements.",
    "what is": "This refers to a fundamental concept in computer science. It's important to understand both its definition and practical applications.\n\nKey points:\n- It's a core component of computing systems\n- It relates to how data is processed and stored\n- Understanding this concept helps with problem-solving\n\nThe OCR specification requires you to know both theoretical aspects and practical implementations.",
    "how does": "This process works through a series of steps:\n\n1. First, initialization occurs\n2. Then, the main operation takes place\n3. Finally, the result is produced\n\nThis mechanism is essential for understanding how computer systems function efficiently. The OCR exam may ask you to explain this process or compare it with alternatives.",
    "why is": "This is important for several reasons:\n\n- It forms the foundation for more advanced concepts\n- It enables efficient problem-solving in computing\n- It has practical applications in real-world systems\n\nUnderstanding the significance of this concept will help you answer evaluation questions in your exam, where you need to assess importance and impact.",
    "example": "Here's an example to illustrate this concept:\n\n```python\ndef example_function(data):\n    result = process(data)\n    return result\n\n# Usage\noutput = example_function(input_data)\n```\n\nThis demonstrates the basic principles in action. Try to work through this example step by step to understand how it applies the concept we're discussing."
};

function sendMessage() {
    const message = userInput.value.trim();
    if (!message) return;
    
    // Add user message to chat
    addMessage('user', message);
    
    // Update conversation history
    conversationHistory.push({
        role: "user",
        content: message
    });
    
    // Clear input
    userInput.value = '';
    
    // Add loading message
    addMessage('system', 'Thinking...');
    
    // Call the API to get a response
    fetch('/student/chat', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({
            question: message,
            topic_code: topicCode,
            mode: currentMode
        })
    })
    .then(response => response.json())
    .then(data => {
        // Remove loading message
        const loadingMsg = document.querySelector('.message.system:last-child');
        if (loadingMsg) loadingMsg.remove();
        
        if (data.error) {
            // Show error message
            addMessage('system', `Error: ${data.error}`);
        } else {
            // Add response
            addMessage('assistant', data.response);
            
            // Update conversation history
            conversationHistory.push({
                role: "assistant",
                content: data.response
            });
        }
        
        // Scroll to bottom
        chatMessages.scrollTop = chatMessages.scrollHeight;
    })
    .catch(error => {
        console.error('Error:', error);
        const loadingMsg = document.querySelector('.message.system:last-child');
        if (loadingMsg) loadingMsg.remove();
        addMessage('system', `Error: ${error.message}`);
        chatMessages.scrollTop = chatMessages.scrollHeight;
    });
}

function addMessage(role, content) {
    const messageDiv = document.createElement('div');
    messageDiv.classList.add('message', role);
    
    // For assistant messages, parse markdown
    if (role === 'assistant') {
        // Use a simple markdown parser
        content = parseMarkdown(content);
    } else {
        // Escape HTML for user and system messages
        content = escapeHtml(content);
    }
    
    messageDiv.innerHTML = content;
    chatMessages.appendChild(messageDiv);
    
    // Scroll to bottom
    chatMessages.scrollTop = chatMessages.scrollHeight;
}

function parseMarkdown(text) {
    // This is a simplified markdown parser
    // For a production app, use a library like marked.js
    
    // Code blocks
    text = text.replace(/```([\s\S]*?)```/g, '<pre><code>$1</code></pre>');
    
    // Inline code
    text = text.replace(/`([^`]+)`/g, '<code>$1</code>');
    
    // Headers
    text = text.replace(/^# (.*$)/gm, '<h1>$1</h1>');
    text = text.replace(/^## (.*$)/gm, '<h2>$1</h2>');
    text = text.replace(/^### (.*$)/gm, '<h3>$1</h3>');
    
    // Bold
    text = text.replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>');
    
    // Italic
    text = text.replace(/\*(.*?)\*/g, '<em>$1</em>');
    
    // Lists
    text = text.replace(/^\s*\d+\.\s+(.*$)/gm, '<li>$1</li>');
    text = text.replace(/^\s*\*\s+(.*$)/gm, '<li>$1</li>');
    
    // Wrap lists
    text = text.replace(/<li>.*?<\/li>/g, function(match) {
        return '<ul>' + match + '</ul>';
    });
    
    // Remove duplicate ul tags
    text = text.replace(/<\/ul>\s*<ul>/g, '');
    
    // Line breaks
    text = text.replace(/\n/g, '<br>');
    
    return text;
}

function escapeHtml(text) {
    return text
        .replace(/&/g, '&amp;')
        .replace(/</g, '&lt;')
        .replace(/>/g, '&gt;')
        .replace(/"/g, '&quot;')
        .replace(/'/g, '&#039;')
        .replace(/\n/g, '<br>');
}
