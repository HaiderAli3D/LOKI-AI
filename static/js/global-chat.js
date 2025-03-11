// OCR A-Level Computer Science AI Tutor - Global Chat Interface

// Elements
let globalChatMessages;
let globalChatInput;
let globalChatSendBtn;
let globalChatToggle;
let globalChatContainer;

// Initialize global chat
document.addEventListener('DOMContentLoaded', () => {
    console.log('DOM loaded, initializing global chat');
    
    // Get elements
    globalChatMessages = document.getElementById('global-chat-messages');
    globalChatInput = document.getElementById('global-chat-input');
    globalChatSendBtn = document.getElementById('global-chat-send-btn');
    globalChatToggle = document.getElementById('global-chat-toggle');
    globalChatContainer = document.getElementById('global-chat-container');
    
    console.log('Global chat elements:', { globalChatMessages, globalChatInput, globalChatSendBtn, globalChatToggle });
    
    // Set up event listeners
    if (globalChatSendBtn) {
        console.log('Adding click event listener to send button');
        globalChatSendBtn.addEventListener('click', sendGlobalChatMessage);
    }
    
    if (globalChatInput) {
        console.log('Adding keydown event listener to input field');
        globalChatInput.addEventListener('keydown', e => {
            if (e.key === 'Enter' && !e.shiftKey) {
                e.preventDefault();
                sendGlobalChatMessage();
            }
        });
    }
    
    // Set up toggle functionality
    if (globalChatToggle && globalChatContainer) {
        console.log('Adding click event listener to toggle button');
        globalChatToggle.addEventListener('click', toggleGlobalChat);
        
        // Check if there's a saved state in localStorage
        const chatCollapsed = localStorage.getItem('globalChatCollapsed') === 'true';
        if (chatCollapsed) {
            globalChatContainer.classList.add('collapsed');
            // Update toggle button text
            if (globalChatToggle.querySelector('span')) {
                globalChatToggle.querySelector('span').textContent = '▲';
            }
        } else {
            // If not collapsed, set the expanded text
            if (globalChatToggle.querySelector('span')) {
                globalChatToggle.querySelector('span').textContent = '▼ Collapse';
            }
        }
    }
    
    // Clear any existing messages and add a welcome message
    if (globalChatMessages) {
        // Clear existing messages
        globalChatMessages.innerHTML = '';
        // Add welcome message
        addGlobalChatMessage('assistant', 'Welcome to the Computer Science Help chat! Ask any A-Level CS question here and I\'ll provide a fresh, tailored response.');
    }
});

// Toggle chat between expanded and collapsed states
function toggleGlobalChat() {
    if (globalChatContainer) {
        globalChatContainer.classList.toggle('collapsed');
        
        // Update toggle button text
        if (globalChatToggle.querySelector('span')) {
            const isCollapsed = globalChatContainer.classList.contains('collapsed');
            globalChatToggle.querySelector('span').textContent = isCollapsed ? '▲' : '▼ Collapse';
        }
        
        // Save state to localStorage
        const isCollapsed = globalChatContainer.classList.contains('collapsed');
        localStorage.setItem('globalChatCollapsed', isCollapsed);
    }
}

// Track conversation history
let globalChatHistory = [];

// Send message
function sendGlobalChatMessage() {
    if (!globalChatInput) return;
    
    const message = globalChatInput.value.trim();
    if (!message) return;
    
    // Get current time
    const now = new Date();
    const timeString = now.toLocaleTimeString();
    
    // Append context info to message
    const contextTag = `[CONTEXT: General Learning | ${timeString}]`;
    const messageWithContext = `${message}\n\n${contextTag}`;
    
    // Add user message to chat (without showing the context tag to the user)
    addGlobalChatMessage('user', message);
    
    // Update conversation history with context
    globalChatHistory.push({
        role: "user",
        content: messageWithContext
    });
    
    // Clear input
    globalChatInput.value = '';
    
    // Add loading message
    addGlobalChatMessage('system', 'Thinking...');
    
    // Call the API to get a response
    fetch('/global-chat', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({
            question: messageWithContext
        })
    })
    .then(response => response.json())
    .then(data => {
        // Remove loading message
        const loadingMsg = globalChatMessages.querySelector('.message.system:last-child');
        if (loadingMsg) loadingMsg.remove();
        
        if (data.error) {
            // Show error message
            addGlobalChatMessage('system', `Error: ${data.error}`);
        } else {
            // Add response
            addGlobalChatMessage('assistant', data.response);
            
            // Update conversation history
            globalChatHistory.push({
                role: "assistant",
                content: data.response
            });
        }
        
        // Scroll to bottom
        globalChatMessages.scrollTop = globalChatMessages.scrollHeight;
    })
    .catch(error => {
        console.error('Error:', error);
        const loadingMsg = globalChatMessages.querySelector('.message.system:last-child');
        if (loadingMsg) loadingMsg.remove();
        addGlobalChatMessage('system', `Error: ${error.message}`);
        globalChatMessages.scrollTop = globalChatMessages.scrollHeight;
    });
}

// Add message to chat
function addGlobalChatMessage(role, content) {
    if (!globalChatMessages) return;
    
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
    globalChatMessages.appendChild(messageDiv);
    
    // Scroll to bottom
    globalChatMessages.scrollTop = globalChatMessages.scrollHeight;
}

// Parse markdown (reusing from chat.js)
function parseMarkdown(text) {
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

// Escape HTML (reusing from chat.js)
function escapeHtml(text) {
    return text
        .replace(/&/g, '&amp;')
        .replace(/</g, '&lt;')
        .replace(/>/g, '&gt;')
        .replace(/"/g, '&quot;')
        .replace(/'/g, '&#039;')
        .replace(/\n/g, '<br>');
}
