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
        addGlobalChatMessage('assistant', 'Welcome to the Computer Science Help chat! Ask any A-Level CS question here.');
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

// Pre-written responses for global chat
const globalChatResponses = {
    "default": "This is an important concept in A-Level Computer Science. The OCR specification covers this in detail, and you should make sure you understand both the theoretical and practical aspects.\n\nKey points to remember:\n- How this concept fits into the broader curriculum\n- The practical applications in real-world systems\n- How to apply this knowledge in exam questions\n\nRefer to your textbook for more detailed explanations and examples.",
    "hardware": "Hardware refers to the physical components of a computer system. Key hardware components include:\n\n- CPU (Central Processing Unit)\n- Memory (RAM, ROM, Cache)\n- Storage devices (HDD, SSD, etc.)\n- Input/Output devices\n\nThe OCR specification requires you to understand how these components work together and their individual characteristics.",
    "software": "Software refers to programs and data that run on computer hardware. There are two main types:\n\n1. Systems software (OS, utilities, drivers)\n2. Applications software (productivity apps, games, etc.)\n\nThe development process includes analysis, design, implementation, testing, and evaluation phases. Understanding the different types of programming languages and their uses is also important.",
    "programming": "Programming involves creating instructions for computers to follow. Key concepts include:\n\n- Variables and data types\n- Control structures (sequence, selection, iteration)\n- Procedures and functions\n- Data structures (arrays, records, etc.)\n\nThe OCR specification requires you to understand these concepts and be able to apply them in practical programming tasks.",
    "data": "Data representation is a fundamental concept in computing. You need to understand:\n\n- Binary, hexadecimal, and decimal number systems\n- Character encoding (ASCII, Unicode)\n- Image representation\n- Sound representation\n- Data compression techniques\n\nBeing able to convert between different number systems and calculate file sizes is important for the exam.",
    "networking": "Computer networks allow devices to communicate and share resources. Key concepts include:\n\n- Network topologies (star, bus, mesh, etc.)\n- Protocols (TCP/IP, HTTP, FTP, etc.)\n- Network hardware (routers, switches, etc.)\n- Security measures\n\nThe OCR specification requires you to understand how networks function and the advantages/disadvantages of different configurations."
};

// Track conversation history
let globalChatHistory = [];

// Send message
function sendGlobalChatMessage() {
    if (!globalChatInput) return;
    
    const message = globalChatInput.value.trim();
    if (!message) return;
    
    // Add user message to chat
    addGlobalChatMessage('user', message);
    
    // Update conversation history
    globalChatHistory.push({
        role: "user",
        content: message
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
            question: message
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
