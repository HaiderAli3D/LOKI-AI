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

// Function to create initial prompt with context information
function create_initial_prompt_with_context(topic_code, topic_title, mode, timeString) {
    // Base message based on the current mode
    let basePrompt = "";
    
    if (mode === "explore") {
        basePrompt = `I'd like to learn about ${topic_title} from the OCR A-Level Computer Science curriculum. Please provide a comprehensive explanation.`;
    } else if (mode === "practice") {
        basePrompt = `I'd like to practice ${topic_title} from the OCR A-Level Computer Science curriculum. Please provide practice questions.`;
    } else if (mode === "code") {
        basePrompt = `I'd like to learn about ${topic_title} through practical coding examples. Please provide code examples and explanations.`;
    } else if (mode === "review") {
        basePrompt = `I'd like to review ${topic_title}. Please create a comprehensive revision summary.`;
    } else if (mode === "test") {
        basePrompt = `I'd like to test my knowledge of ${topic_title}. Please create a mini-assessment with exam-style questions.`;
    } else {
        basePrompt = `I'd like to learn about ${topic_title} from the OCR A-Level Computer Science curriculum. Please help me understand this topic in detail.`;
    }
    
    // Append context tag
    return `${basePrompt}\n\n[CONTEXT: Topic ${topic_code} ${topic_title} | ${timeString}]`;
}

function sendInitialPrompt() {
    // Clear chat
    chatMessages.innerHTML = '';
    
    // Add loading message
    addMessage('system', 'Loading...');
    
    // Reset conversation history
    conversationHistory = [];
    
    // Get current time
    const now = new Date();
    const timeString = now.toLocaleTimeString();
    
    // Create context tag for the initial message
    const initialPrompt = create_initial_prompt_with_context(topicCode, topicTitle, currentMode, timeString);
    
    // Call the API to get an initial response
    fetch('/student/initial-prompt', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({
            topic_code: topicCode,
            mode: currentMode
        })
    })
    .then(response => response.json())
    .then(data => {
        // Remove loading message
        chatMessages.innerHTML = '';
        
        if (data.error) {
            // Show error message
            addMessage('system', `Error: ${data.error}`);
        } else {
            // Add response
            addMessage('assistant', data.response);
            
            // Add the initial prompt with context to conversation history
            conversationHistory.push({
                role: "user",
                content: initialPrompt
            });
            
            // Add the assistant's response to conversation history
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
        chatMessages.innerHTML = '';
        addMessage('system', `Error: ${error.message}`);
        chatMessages.scrollTop = chatMessages.scrollHeight;
    });
}

function sendMessage() {
    const message = userInput.value.trim();
    if (!message) return;
    
    // Get current time
    const now = new Date();
    const timeString = now.toLocaleTimeString();
    
    // Append context info to message
    const contextTag = `[CONTEXT: Topic ${topicCode} ${topicTitle} | ${timeString}]`;
    const messageWithContext = `${message}\n\n${contextTag}`;
    
    // Add user message to chat (without showing the context tag to the user)
    addMessage('user', message);
    
    // Update conversation history with context
    conversationHistory.push({
        role: "user",
        content: messageWithContext
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
            question: messageWithContext,
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
