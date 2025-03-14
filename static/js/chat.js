// OCR A-Level Computer Science AI Tutor - Chat Interface

// Elements
const chatMessages = document.getElementById('chat-messages');
const userInput = document.getElementById('user-input');
const sendButton = document.getElementById('send-btn');
const modeBtns = document.querySelectorAll('.mode-btn');
const rateBtn = document.getElementById('rate-understanding-btn');
const examBtn = document.getElementById('record-exam-btn');
const refreshBtn = document.getElementById('refresh-chat-btn');
const rateModal = document.getElementById('rate-modal');
const examModal = document.getElementById('exam-modal');
const closeBtns = document.querySelectorAll('.close-modal');
const rateForm = document.getElementById('rate-form');
const examForm = document.getElementById('exam-form');

// Initialize chat when page loads
window.addEventListener('DOMContentLoaded', () => {
    // Check if we have a session ID for this topic already
    const topicSessionKey = `session_${topicCode}`;
    const savedSessionId = localStorage.getItem(topicSessionKey);
    
    if (savedSessionId) {
        // We have an existing session, try to load it
        sessionDBId = savedSessionId;
        console.log("Found existing session ID:", sessionDBId);
        loadRecentMessages();
    } else {
        // No existing session, start a new one
        console.log("No existing session found, starting fresh");
        sendInitialPrompt();
    }
});

// Function to load recent messages
function loadRecentMessages() {
    // Clear any existing messages
    chatMessages.innerHTML = '';
    
    // Add loading message
    const loadingDiv = document.createElement('div');
    loadingDiv.classList.add('message', 'system');
    loadingDiv.innerHTML = "Loading previous messages...";
    chatMessages.appendChild(loadingDiv);
    
    console.log("Loading messages for session:", sessionDBId);
    
    // Fetch recent messages from server
    fetch('/student/get-recent-messages', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({
            session_id: sessionDBId
        })
    })
    .then(response => {
        if (!response.ok) {
            throw new Error(`HTTP error! Status: ${response.status}`);
        }
        return response.json();
    })
    .then(data => {
        // Remove loading message
        loadingDiv.remove();
        
        if (data.error) {
            console.error("Error loading messages:", data.error);
            addMessage('system', `Error: ${data.error}`);
            // If there was an error, fall back to initial prompt
            sendInitialPrompt();
            return;
        }
        
        console.log(`Loaded ${data.messages ? data.messages.length : 0} messages`);
        
        if (!data.messages || data.messages.length === 0) {
            // No messages found, send initial prompt
            sendInitialPrompt();
            return;
        }
        
        // Reset conversation history
        conversationHistory = [];
        
        // Check if the last message is from the user and needs a response
        let userHasLastMessage = false;
        let lastMessageIdx = data.messages.length - 1;
        
        if (data.messages[lastMessageIdx] && data.messages[lastMessageIdx].role === 'user') {
            userHasLastMessage = true;
        }
        
        // Add messages to the chat (filtering system prompts)
        data.messages.forEach(msg => {
            // Detect if this is an initial/system prompt that should be hidden
            const isInitialPrompt = msg.role === 'user' && (
                // Match standard mode prompts
                msg.content.includes('I\'d like to learn about') || 
                msg.content.includes('I\'d like to practice') || 
                msg.content.includes('I\'d like to test') || 
                msg.content.includes('I\'d like to review') ||
                msg.content.includes('I\'d like to code') ||
                // Match mode change prompts
                msg.content.includes('I\'d like to explore') ||
                // More extensive checking for default prompts
                msg.content.includes('The goal of this mode is to') ||
                msg.content.includes('You are now teaching the user about') ||
                msg.content.includes('You are now helping the user practice') ||
                msg.content.includes('Please create a practice assessment') ||
                // Check for mode change markers
                (msg.content.includes(`I'd like to ${currentMode}`) && msg.content.includes('[CONTEXT:'))
            );
            
            console.log(`Message role: ${msg.role}, isInitialPrompt: ${isInitialPrompt}, First 40 chars: ${msg.content.substring(0, 40)}...`);
            
            // Always add all messages to conversation history for Claude
            conversationHistory.push({
                role: msg.role,
                content: msg.content
            });
            
            // Only display non-system, non-initial prompt messages in the UI
            if (!isInitialPrompt && msg.role !== 'system') {
                // Remove context tags if present
                let displayContent = msg.content;
                if (displayContent.includes('[CONTEXT:')) {
                    displayContent = displayContent.split('\n\n[CONTEXT:')[0];
                }
                
                // Remove mode tags if present
                if (displayContent.includes('[MODE:')) {
                    displayContent = displayContent.split('\n\n[MODE:')[0];
                }
                
                addMessage(msg.role, displayContent);
            }
        });
        
        // Scroll to bottom
        chatMessages.scrollTop = chatMessages.scrollHeight;
        
        // If the last message was from the user, get AI response
        if (userHasLastMessage) {
            // Send the last user message to get a response
            const lastUserMessage = data.messages[lastMessageIdx].content;
            getAIResponseToExistingMessage(lastUserMessage);
        }
    })
    .catch(error => {
        console.error('Error loading messages:', error);
        loadingDiv.remove();
        addMessage('system', 'Failed to load previous messages. Starting new conversation.');
        sendInitialPrompt();
    });
}

// Function to get AI response to an existing user message
function getAIResponseToExistingMessage(userMessage) {
    // Create message div for assistant
    const messageDiv = document.createElement('div');
    messageDiv.classList.add('message', 'assistant');
    chatMessages.appendChild(messageDiv);
    
    // Display "thinking..." message initially
    messageDiv.innerHTML = "<em>Thinking...</em>";
    
    // Add unique request ID to track this specific request
    const requestId = Date.now().toString();
    
    // Call the API to get a response to the existing message
    fetch('/student/chat', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({
            question: userMessage,
            topic_code: topicCode,
            mode: currentMode,
            stream: true,
            request_id: requestId,
            session_id: sessionDBId
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
            messageDiv.remove();
            addMessage('system', `Error: ${data.error}`);
            return;
        }
        
        // Set up streaming with the unique request ID
        let fullResponse = '';
        
        // Connect to the SSE endpoint with request ID
        const source = new EventSource(`/student/chat?request_id=${requestId}`);
        
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
                    
                    // Add the assistant's response to conversation history
                    conversationHistory.push({
                        role: "assistant",
                        content: fullResponse
                    });
                    
                    // If we have a session ID in the database, save the response there too
                    if (sessionDBId) {
                        fetch('/student/save-response', {
                            method: 'POST',
                            headers: {
                                'Content-Type': 'application/json'
                            },
                            body: JSON.stringify({
                                session_id: sessionDBId,
                                response: fullResponse
                            })
                        }).catch(error => {
                            console.error('Error saving response to database:', error);
                        });
                    }
                    
                    return;
                }
                
                if (data.text) {
                    fullResponse += data.text;
                    messageDiv.innerHTML = parseMarkdown(fullResponse);
                    chatMessages.scrollTop = chatMessages.scrollHeight;
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
                addMessage('system', 'Error: Failed to get a response. Please try again.');
            }
        };
    })
    .catch(error => {
        console.error('Error:', error);
        messageDiv.remove();
        addMessage('system', `Error: ${error.message}`);
        chatMessages.scrollTop = chatMessages.scrollHeight;
    });
}

// Mode selection
modeBtns.forEach(btn => {
    btn.addEventListener('click', () => {
        // Update active button
        modeBtns.forEach(b => b.classList.remove('active'));
        btn.classList.add('active');
        
        const newMode = btn.dataset.mode;
        
        // Only trigger a new prompt if the mode actually changed
        if (currentMode !== newMode) {
            // Update current mode
            currentMode = newMode;
            
            // Show/hide PDF generation button based on mode
            const generatePdfBtn = document.getElementById('generate-pdf-btn');
            if (currentMode === 'test') {
                generatePdfBtn.style.display = 'flex';
            } else {
                generatePdfBtn.style.display = 'none';
            }
            
            // Create a mode change prompt (which won't be shown to the user)
            const now = new Date();
            const timeString = now.toLocaleTimeString();
            const modePrompt = `I'd like to ${currentMode} ${topicTitle}.\n\n[CONTEXT: Topic ${topicCode} ${topicTitle} | ${timeString}]`;
            
            // Add to conversation history but don't display in UI
            conversationHistory.push({
                role: "user",
                content: modePrompt
            });
            
            // Create message div for assistant
            const messageDiv = document.createElement('div');
            messageDiv.classList.add('message', 'assistant');
            chatMessages.appendChild(messageDiv);
            
            // Display "thinking..." message initially
            messageDiv.innerHTML = "<em>Thinking...</em>";
            
            // Add unique request ID to track this specific request
            const requestId = Date.now().toString();
            
            // Send the mode change request
            fetch('/student/chat', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    question: modePrompt,
                    topic_code: topicCode,
                    mode: currentMode,
                    stream: true,
                    request_id: requestId,
                    session_id: sessionDBId
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
                    messageDiv.remove();
                    addMessage('system', `Error: ${data.error}`);
                    return;
                }
                
                // Set up streaming with the unique request ID
                let fullResponse = '';
                
                // Connect to the SSE endpoint with request ID
                const source = new EventSource(`/student/chat?request_id=${requestId}`);
                
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
                            
                            // Add the assistant's response to conversation history
                            conversationHistory.push({
                                role: "assistant",
                                content: fullResponse
                            });
                            
                            // If we have a session ID in the database, save the response there too
                            if (sessionDBId) {
                                fetch('/student/save-response', {
                                    method: 'POST',
                                    headers: {
                                        'Content-Type': 'application/json'
                                    },
                                    body: JSON.stringify({
                                        session_id: sessionDBId,
                                        response: fullResponse
                                    })
                                }).catch(error => {
                                    console.error('Error saving response to database:', error);
                                });
                            }
                            
                            return;
                        }
                        
                        if (data.text) {
                            fullResponse += data.text;
                            messageDiv.innerHTML = parseMarkdown(fullResponse);
                            chatMessages.scrollTop = chatMessages.scrollHeight;
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
                        addMessage('system', 'Error: Failed to get a response. Please try again.');
                    }
                };
            })
            .catch(error => {
                console.error('Error:', error);
                messageDiv.remove();
                addMessage('system', `Error: ${error.message}`);
                chatMessages.scrollTop = chatMessages.scrollHeight;
            });
        }
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

// PDF Generation button
document.getElementById('generate-pdf-btn').addEventListener('click', generatePDF);

function generatePDF() {
    // Find the latest message that contains LaTeX content
    let latexContent = null;
    let lastAssistantMessage = null;
    
    if (conversationHistory.length > 0) {
        // First, try to find a message with LaTeX code markers
        for (let i = conversationHistory.length - 1; i >= 0; i--) {
            if (conversationHistory[i].role === 'assistant') {
                const messageText = conversationHistory[i].content;
                
                // Save the last assistant message as fallback
                if (!lastAssistantMessage) {
                    lastAssistantMessage = messageText;
                }
                
                // Look for common LaTeX document markers
                if (messageText.includes('\\documentclass') || 
                    messageText.includes('\\begin{document}')) {
                    latexContent = messageText;
                    break;
                }
            }
        }
        
        // If no LaTeX content found, use the last assistant message
        if (!latexContent && lastAssistantMessage) {
            latexContent = lastAssistantMessage;
        }
    }
    
    if (!latexContent) {
        alert('No content available to generate PDF');
        return;
    }
    
    // Show loading indicator
    const loadingDiv = document.createElement('div');
    loadingDiv.classList.add('message', 'system');
    loadingDiv.innerHTML = "Generating LaTeX PDF... This may take a moment.";
    chatMessages.appendChild(loadingDiv);
    chatMessages.scrollTop = chatMessages.scrollHeight;
    
    // Make API request
    fetch('/generate-exam-pdf', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({
            topic_title: topicTitle,
            content: latexContent,
            topic_code: topicCode
        })
    })
    .then(response => response.json())
    .then(data => {
        // Remove loading indicator
        loadingDiv.remove();
        
        if (data.error) {
            throw new Error(data.error);
        }
        
        if (data.success && data.pdf_url) {
            // Open PDF in new tab
            window.open(data.pdf_url, '_blank');
            
            // Show success message with link to PDF library
            const successDiv = document.createElement('div');
            successDiv.classList.add('message', 'system');
            successDiv.innerHTML = `
                PDF generated successfully and opened in a new tab! 
                <a href="/student/pdf-library">View all your PDFs</a>
            `;
            chatMessages.appendChild(successDiv);
        } else {
            throw new Error('Failed to generate PDF');
        }
        
        chatMessages.scrollTop = chatMessages.scrollHeight;
    })
    .catch(error => {
        console.error('Error generating PDF:', error);
        loadingDiv.innerHTML = `Error generating PDF: ${error.message}`;
    });
}

// Refresh button to clear chat
refreshBtn.addEventListener('click', () => {
    if (confirm('Are you sure you want to clear the chat and start a new conversation?')) {
        // Clear UI
        chatMessages.innerHTML = '';
        
        // Clear local conversation history
        conversationHistory = [];
        
        // Remove the session from localStorage
        const topicSessionKey = `session_${topicCode}`;
        localStorage.removeItem(topicSessionKey);
        
        // Clear the database entries
        clearChatHistory();
        
        // Start a new conversation after a short delay
        setTimeout(() => {
            sendInitialPrompt();
        }, 500);
    }
});

// Function to clear chat history from the database
function clearChatHistory() {
    if (!sessionDBId) return;
    
    console.log("Clearing chat history for session:", sessionDBId);
    
    fetch('/student/clear-chat-history', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({
            session_id: sessionDBId
        })
    })
    .then(response => response.json())
    .then(data => {
        if (data.error) {
            console.error('Error clearing chat history:', data.error);
            addMessage('system', `Error clearing chat history: ${data.error}`);
        } else {
            console.log('Chat history cleared successfully');
            // Reset session ID to force creation of a new session
            sessionDBId = null;
        }
    })
    .catch(error => {
        console.error('Error clearing chat history:', error);
    });
}

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
    
    const score = document.getElementById('score').value;
    const maxScore = document.getElementById('max-score').value;
    
    if (parseInt(score) > parseInt(maxScore)) {
        alert('Score cannot be greater than maximum score');
        return;
    }
    
    // Send exam score to server (with default values for question_type and difficulty)
    fetch('/student/record-exam', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({
            topic_code: topicCode,
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
    
    // Check if this is a sub-topic by counting the dots in the topic code
    let isSubTopic = topic_code.split('.').length > 2;
    let parentTopicCode = isSubTopic ? topic_code.split('.').slice(0, 2).join('.') : topic_code;
    
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
    
    // Reset conversation history
    conversationHistory = [];
    
    // Get current time
    const now = new Date();
    const timeString = now.toLocaleTimeString();
    
    // Create context tag for the initial message
    const initialPrompt = create_initial_prompt_with_context(topicCode, topicTitle, currentMode, timeString);
    
    // Add the initial prompt with context to conversation history (but don't display it in the UI)
    conversationHistory.push({
        role: "user",
        content: initialPrompt
    });
    
    // Display loading indicator
    const loadingDiv = document.createElement('div');
    loadingDiv.classList.add('message', 'system');
    loadingDiv.innerHTML = "Loading your AI tutor...";
    chatMessages.appendChild(loadingDiv);
    
    // Create message div for assistant
    const messageDiv = document.createElement('div');
    messageDiv.classList.add('message', 'assistant');
    chatMessages.appendChild(messageDiv);
    
    // Display "thinking..." message initially
    messageDiv.innerHTML = "<em>Thinking...</em>";
    
    // Add unique request ID to track this specific request
    const requestId = Date.now().toString();
    
    // Call the API to initiate streaming for initial prompt
    fetch('/student/initial-prompt', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({
            topic_code: topicCode,
            mode: currentMode,
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
            loadingDiv.remove();
            messageDiv.remove();
            addMessage('system', `Error: ${data.error}`);
            return;
        }
        
        // Store the session ID if it was returned from the server
        if (data.session_id) {
            sessionDBId = data.session_id;
            // Save this session ID in localStorage for this topic
            const topicSessionKey = `session_${topicCode}`;
            localStorage.setItem(topicSessionKey, sessionDBId);
            console.log("Created and saved new session ID:", sessionDBId);
        }
        
        // Remove the loading message
        loadingDiv.remove();
        
        // Set up streaming with the unique request ID
        let fullResponse = '';
        
        // Connect to the SSE endpoint with request ID
        const source = new EventSource(`/student/chat?request_id=${requestId}`);
        
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
                    
                    // Add the assistant's response to conversation history
                    conversationHistory.push({
                        role: "assistant",
                        content: fullResponse
                    });
                    
                    // If we have a session ID in the database, save the response there too
                    if (sessionDBId) {
                        fetch('/student/save-response', {
                            method: 'POST',
                            headers: {
                                'Content-Type': 'application/json'
                            },
                            body: JSON.stringify({
                                session_id: sessionDBId,
                                response: fullResponse
                            })
                        }).catch(error => {
                            console.error('Error saving response to database:', error);
                        });
                    }
                    
                    return;
                }
                
                if (data.text) {
                    fullResponse += data.text;
                    messageDiv.innerHTML = parseMarkdown(fullResponse);
                    chatMessages.scrollTop = chatMessages.scrollHeight;
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
                addMessage('system', 'Error: Failed to get a response. Please try again.');
            }
        };
    })
    .catch(error => {
        console.error('Error:', error);
        messageDiv.remove();
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
    
    // Create message div for assistant
    const messageDiv = document.createElement('div');
    messageDiv.classList.add('message', 'assistant');
    chatMessages.appendChild(messageDiv);
    
    // Display "thinking..." message initially
    messageDiv.innerHTML = "<em>Thinking...</em>";
    
    // Add unique request ID to track this specific request
    const requestId = Date.now().toString();
    
    // Send POST request to initiate streaming
    fetch('/student/chat', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({
            question: messageWithContext,
            topic_code: topicCode,
            mode: currentMode,
            stream: true,
            request_id: requestId,
            session_id: sessionDBId
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
        
        // Make sure the response indicates success before trying to stream
        if (!data.success) {
            throw new Error('The server did not acknowledge streaming request');
        }
        
        // Set up streaming with the unique request ID
        let fullResponse = '';
        
        // Connect to the SSE endpoint with request ID
        const source = new EventSource(`/student/chat?request_id=${requestId}`);
        
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
                    conversationHistory.push({
                        role: "assistant",
                        content: fullResponse
                    });
                    
                    // If we have a session ID in the database, save the response there too
                    if (sessionDBId) {
                        fetch('/student/save-response', {
                            method: 'POST',
                            headers: {
                                'Content-Type': 'application/json'
                            },
                            body: JSON.stringify({
                                session_id: sessionDBId,
                                response: fullResponse
                            })
                        }).catch(error => {
                            console.error('Error saving response to database:', error);
                        });
                    }
                    
                    return;
                }
                
                if (data.text) {
                    fullResponse += data.text;
                    messageDiv.innerHTML = parseMarkdown(fullResponse);
                    chatMessages.scrollTop = chatMessages.scrollHeight;
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
                addMessage('system', 'Error: Failed to get a response. Please try again.');
            }
        };
    })
    .catch(error => {
        console.error('Network error:', error);
        messageDiv.remove();
        addMessage('system', `Error: ${error.message}`);
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
