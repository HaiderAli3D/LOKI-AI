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
        
        // Initialize sidebar state (default is docked)
        const pageContainer = document.querySelector('.page-with-pdf-and-chat');
        const savedState = localStorage.getItem('globalChatDocked');
        
        // If the user has previously set a preference to not be docked, use that
        if (savedState === 'false') {
            globalChatContainer.classList.remove('docked');
            if (pageContainer) {
                pageContainer.classList.remove('chat-docked');
            }
        } else {
            // Otherwise ensure the docked state is applied
            globalChatContainer.classList.add('docked');
            if (pageContainer) {
                pageContainer.classList.add('chat-docked');
            }
            localStorage.setItem('globalChatDocked', 'true');
        }
    }
    
    // Initialize or reset global chat messages
    if (globalChatMessages) {
        // Check if messages already exist
        if (globalChatMessages.childElementCount === 0) {
            // Only add welcome message if container is empty
            addGlobalChatMessage('assistant', 'Welcome to the Computer Science Help chat! Ask any A-Level CS question here and I\'ll provide a fresh, tailored response.');
        }
    }
});

// Toggle chat between expanded and docked states
function toggleGlobalChat() {
    if (globalChatContainer) {
        const pageContainer = document.querySelector('.page-with-pdf-and-chat');
        const isDocked = globalChatContainer.classList.contains('docked');
        
        if (isDocked) {
            // Expand the chat
            globalChatContainer.classList.remove('docked');
            if (pageContainer) {
                pageContainer.classList.remove('chat-docked');
            }
            localStorage.setItem('globalChatDocked', 'false');
        } else {
            // Dock the chat
            globalChatContainer.classList.add('docked');
            if (pageContainer) {
                pageContainer.classList.add('chat-docked');
            }
            localStorage.setItem('globalChatDocked', 'true');
        }
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
    
    // Create message div for assistant
    const messageDiv = document.createElement('div');
    messageDiv.classList.add('message', 'assistant');
    if (globalChatMessages) {
        globalChatMessages.appendChild(messageDiv);
    }
    
    // Display "thinking..." message initially
    messageDiv.innerHTML = "<em>Thinking...</em>";
    
    // Add unique request ID to track this specific request
    const requestId = Date.now().toString();
    
    // Send POST request to initiate streaming
    fetch('/global-chat', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({
            question: messageWithContext,
            stream: true,
            request_id: requestId
        })
    })
    .then(response => {
        if (!response.ok) {
            throw new Error('Network response was not ok');
        }
        return response.json();
    })
    .then(data => {
        if (data.error) {
            throw new Error(data.error);
        }
        
        // Set up streaming with the unique request ID
        let fullResponse = '';
        
        // Connect to the SSE endpoint with request ID
        const source = new EventSource(`/global-chat?request_id=${requestId}`);
        
        source.onmessage = function(event) {
            try {
                const data = JSON.parse(event.data);
                
                if (data.connected) {
                    // Just a connection confirmation, ignore
                    return;
                }
                
                if (data.done) {
                    source.close();
                    
                    // If we have full_response, use it
                    if (data.full_response) {
                        fullResponse = data.full_response;
                        messageDiv.innerHTML = parseMarkdown(fullResponse);
                    }
                    
                    // Update conversation history
                    globalChatHistory.push({
                        role: "assistant",
                        content: fullResponse
                    });
                    
                    // Keep conversation history at a reasonable size
                    if (globalChatHistory.length > 20) {
                        globalChatHistory = globalChatHistory.slice(-20);
                    }
                    
                    return;
                }
                
                if (data.text) {
                    fullResponse += data.text;
                    messageDiv.innerHTML = parseMarkdown(fullResponse);
                    if (globalChatMessages) {
                        globalChatMessages.scrollTop = globalChatMessages.scrollHeight;
                    }
                }
            } catch (error) {
                console.error('Error parsing SSE message:', error, event.data);
            }
        };
        
        source.onerror = function(error) {
            console.error('EventSource error:', error);
            source.close();
            
            if (fullResponse === '') {
                messageDiv.remove();
                addGlobalChatMessage('system', 'Error: Failed to get a response. Please try again.');
            }
        };
    })
    .catch(error => {
        console.error('Network error:', error);
        messageDiv.remove();
        addGlobalChatMessage('system', `Error: ${error.message}`);
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
