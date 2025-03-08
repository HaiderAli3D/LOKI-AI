/**
 * Main JavaScript file for OCR A-Level Computer Science AI Tutor
 */

// Wait for the DOM to be fully loaded
document.addEventListener('DOMContentLoaded', function() {
    // Initialize tooltips
    $('[data-toggle="tooltip"]').tooltip();
    
    // Initialize popovers
    $('[data-toggle="popover"]').popover();
    
    // Flash message auto-dismiss
    const flashMessages = document.querySelectorAll('.alert:not(.alert-permanent)');
    flashMessages.forEach(function(message) {
        setTimeout(function() {
            $(message).fadeOut('slow');
        }, 5000);
    });
    
    // Password strength meter
    const passwordInput = document.getElementById('password');
    const confirmPasswordInput = document.getElementById('confirm_password');
    
    if (passwordInput) {
        passwordInput.addEventListener('input', function() {
            checkPasswordStrength(this.value);
        });
    }
    
    if (passwordInput && confirmPasswordInput) {
        confirmPasswordInput.addEventListener('input', function() {
            checkPasswordMatch(passwordInput.value, this.value);
        });
    }
    
    // Form validation
    const forms = document.querySelectorAll('.needs-validation');
    Array.from(forms).forEach(function(form) {
        form.addEventListener('submit', function(event) {
            if (!form.checkValidity()) {
                event.preventDefault();
                event.stopPropagation();
            }
            form.classList.add('was-validated');
        }, false);
    });
});

/**
 * Check password strength and update UI
 * @param {string} password - The password to check
 */
function checkPasswordStrength(password) {
    const strengthMeter = document.getElementById('password-strength-meter');
    const strengthText = document.getElementById('password-strength-text');
    
    if (!strengthMeter || !strengthText) return;
    
    // Reset
    strengthMeter.value = 0;
    strengthText.textContent = '';
    
    if (password.length === 0) return;
    
    // Calculate strength
    let strength = 0;
    
    // Length check
    if (password.length >= 8) strength += 1;
    if (password.length >= 12) strength += 1;
    
    // Character type checks
    if (/[a-z]/.test(password)) strength += 1;
    if (/[A-Z]/.test(password)) strength += 1;
    if (/[0-9]/.test(password)) strength += 1;
    if (/[^a-zA-Z0-9]/.test(password)) strength += 1;
    
    // Update UI
    strengthMeter.value = strength;
    
    // Set text based on strength
    let strengthLabel = '';
    let strengthClass = '';
    
    switch (true) {
        case (strength <= 2):
            strengthLabel = 'Weak';
            strengthClass = 'text-danger';
            break;
        case (strength <= 4):
            strengthLabel = 'Moderate';
            strengthClass = 'text-warning';
            break;
        default:
            strengthLabel = 'Strong';
            strengthClass = 'text-success';
    }
    
    strengthText.textContent = strengthLabel;
    strengthText.className = strengthClass;
}

/**
 * Check if passwords match and update UI
 * @param {string} password - The original password
 * @param {string} confirmPassword - The confirmation password
 */
function checkPasswordMatch(password, confirmPassword) {
    const matchText = document.getElementById('password-match-text');
    
    if (!matchText) return;
    
    if (confirmPassword.length === 0) {
        matchText.textContent = '';
        return;
    }
    
    if (password === confirmPassword) {
        matchText.textContent = 'Passwords match';
        matchText.className = 'text-success';
    } else {
        matchText.textContent = 'Passwords do not match';
        matchText.className = 'text-danger';
    }
}

/**
 * Format a date string
 * @param {string} dateString - ISO date string
 * @returns {string} Formatted date string
 */
function formatDate(dateString) {
    if (!dateString) return '';
    
    const date = new Date(dateString);
    return date.toLocaleDateString('en-GB', {
        day: 'numeric',
        month: 'short',
        year: 'numeric'
    });
}

/**
 * Format a duration in seconds
 * @param {number} seconds - Duration in seconds
 * @returns {string} Formatted duration string
 */
function formatDuration(seconds) {
    if (!seconds) return '0m';
    
    const hours = Math.floor(seconds / 3600);
    const minutes = Math.floor((seconds % 3600) / 60);
    
    if (hours > 0) {
        return `${hours}h ${minutes}m`;
    } else {
        return `${minutes}m`;
    }
}

/**
 * Show a confirmation dialog
 * @param {string} message - The confirmation message
 * @param {Function} callback - Function to call if confirmed
 */
function confirmAction(message, callback) {
    if (confirm(message)) {
        callback();
    }
}

/**
 * Handle AJAX form submission
 * @param {HTMLFormElement} form - The form element
 * @param {Function} successCallback - Function to call on success
 * @param {Function} errorCallback - Function to call on error
 */
function submitFormAjax(form, successCallback, errorCallback) {
    const formData = new FormData(form);
    const url = form.action;
    const method = form.method.toUpperCase();
    
    fetch(url, {
        method: method,
        body: formData,
        headers: {
            'X-Requested-With': 'XMLHttpRequest'
        }
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            if (successCallback) successCallback(data);
        } else {
            if (errorCallback) errorCallback(data);
        }
    })
    .catch(error => {
        console.error('Error:', error);
        if (errorCallback) errorCallback({ error: 'An unexpected error occurred' });
    });
}
