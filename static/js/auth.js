/**
 * Common authentication JavaScript utilities
 */

document.addEventListener('DOMContentLoaded', function() {
    // Handle Firebase authentication status changes
    function handleAuthStateChange(user) {
        if (user) {
            console.log('User is signed in:', user.email);
            
            // Get Firebase ID token
            user.getIdToken().then(function(idToken) {
                // Send token to backend
                fetch('/auth/firebase-token', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify({ token: idToken })
                })
                .then(response => response.json())
                .then(data => {
                    if (data.success) {
                        // Redirect to appropriate dashboard
                        window.location.href = data.redirect;
                    } else {
                        console.error('Error with token verification:', data.error);
                    }
                })
                .catch(error => {
                    console.error('Error sending token to backend:', error);
                });
            });
        } else {
            console.log('No user is signed in.');
        }
    }
    
    // Initialize Firebase Authentication observer if Firebase SDK is loaded
    if (typeof firebase !== 'undefined' && firebase.auth) {
        firebase.auth().onAuthStateChanged(handleAuthStateChange);
    }
    
    // Login form submission
    const loginForm = document.getElementById('loginForm');
    if (loginForm) {
        loginForm.addEventListener('submit', function(event) {
            const errorDisplay = document.getElementById('loginError');
            if (errorDisplay) {
                errorDisplay.textContent = '';
                errorDisplay.style.display = 'none';
            }
        });
    }
    
    // Logout functionality
    const logoutButtons = document.querySelectorAll('.logout-button');
    logoutButtons.forEach(button => {
        button.addEventListener('click', function(event) {
            event.preventDefault();
            
            // Sign out from Firebase if available
            if (typeof firebase !== 'undefined' && firebase.auth) {
                firebase.auth().signOut().then(() => {
                    // Navigate to logout route
                    window.location.href = this.getAttribute('href');
                }).catch(error => {
                    console.error('Firebase sign out error:', error);
                    // Still try to navigate to logout route
                    window.location.href = this.getAttribute('href');
                });
            } else {
                // Just navigate to logout route if Firebase not available
                window.location.href = this.getAttribute('href');
            }
        });
    });
});

// Helper function to show authentication error messages
function showAuthError(message, elementId = 'loginError') {
    const errorDisplay = document.getElementById(elementId);
    if (errorDisplay) {
        errorDisplay.textContent = message;
        errorDisplay.style.display = 'block';
    } else {
        alert(message);
    }
}
