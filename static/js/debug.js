// Debug utility functions for OCR A-Level Computer Science AI Tutor
console.log("Debug utilities loaded");

function debugChatState() {
    console.log("---- CHAT DEBUG INFO ----");
    console.log("Topic Code:", topicCode);
    console.log("Topic Title:", topicTitle);
    console.log("Current Mode:", currentMode);
    console.log("Session DB ID:", sessionDBId);
    console.log("Conversation History Length:", conversationHistory ? conversationHistory.length : 0);
    console.log("Chat Messages Count:", chatMessages ? chatMessages.childElementCount : 0);
    console.log("LocalStorage Session ID:", localStorage.getItem(`session_${topicCode}`));
    console.log("------------------------");
    
    // Test database connection
    testDatabaseConnection();
}

function testDatabaseConnection() {
    if (!sessionDBId) {
        console.log("No session ID available to test connection");
        return;
    }
    
    console.log("Testing database connection with session ID:", sessionDBId);
    
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
        console.log("Response status:", response.status);
        return response.json();
    })
    .then(data => {
        console.log("Response data:", data);
        if (data.messages) {
            console.log(`Database has ${data.messages.length} messages for this session`);
        }
    })
    .catch(error => {
        console.error("Database test failed:", error);
    });
}

// Add debug button to the UI
window.addEventListener('DOMContentLoaded', () => {
    const debugBtn = document.createElement('button');
    debugBtn.innerHTML = 'Debug';
    debugBtn.classList.add('btn', 'btn-secondary');
    debugBtn.style.position = 'fixed';
    debugBtn.style.bottom = '10px';
    debugBtn.style.right = '10px';
    debugBtn.style.zIndex = '1000';
    debugBtn.style.opacity = '0.7';
    debugBtn.addEventListener('click', debugChatState);
    document.body.appendChild(debugBtn);
    
    // Run debug once on load
    setTimeout(debugChatState, 2000);
});
