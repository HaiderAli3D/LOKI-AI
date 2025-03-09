/**
 * JavaScript for the registration page
 */

document.addEventListener('DOMContentLoaded', function() {
    // Password strength meter
    const passwordInput = document.getElementById('password');
    const confirmPasswordInput = document.getElementById('confirm_password');
    const passwordStrengthMeter = document.querySelector('.password-strength-meter');
    const submitButton = document.querySelector('button[type="submit"]');
    
    if (passwordInput && passwordStrengthMeter) {
        passwordInput.addEventListener('input', function() {
            const password = this.value;
            const strength = calculatePasswordStrength(password);
            updatePasswordStrengthMeter(strength);
        });
    }
    
    // Confirm password validation
    if (confirmPasswordInput && passwordInput) {
        confirmPasswordInput.addEventListener('input', function() {
            if (this.value !== passwordInput.value) {
                this.setCustomValidity("Passwords don't match");
            } else {
                this.setCustomValidity('');
            }
        });
        
        passwordInput.addEventListener('input', function() {
            if (confirmPasswordInput.value !== '' && this.value !== confirmPasswordInput.value) {
                confirmPasswordInput.setCustomValidity("Passwords don't match");
            } else {
                confirmPasswordInput.setCustomValidity('');
            }
        });
    }
    
    // Form submission
    const registerForm = document.getElementById('registerForm');
    if (registerForm) {
        registerForm.addEventListener('submit', function(event) {
            const password = passwordInput.value;
            const confirmPassword = confirmPasswordInput.value;
            
            // Additional validation before submission
            if (password !== confirmPassword) {
                event.preventDefault();
                alert("Passwords don't match");
                return false;
            }
            
            const strength = calculatePasswordStrength(password);
            if (strength < 2) {
                if (!confirm("Your password is weak. Are you sure you want to continue?")) {
                    event.preventDefault();
                    return false;
                }
            }
            
            return true;
        });
    }
    
    /**
     * Calculate password strength based on various criteria
     * @param {string} password 
     * @returns {number} Strength from 0 (very weak) to 4 (very strong)
     */
    function calculatePasswordStrength(password) {
        let strength = 0;
        
        if (password.length === 0) {
            return strength;
        }
        
        // Length check
        if (password.length >= 8) {
            strength += 1;
        }
        
        // Complexity checks
        if (password.match(/[a-z]+/)) {
            strength += 1;
        }
        
        if (password.match(/[A-Z]+/)) {
            strength += 1;
        }
        
        if (password.match(/[0-9]+/)) {
            strength += 1;
        }
        
        if (password.match(/[^a-zA-Z0-9]+/)) {
            strength += 1;
        }
        
        return Math.min(4, strength);
    }
    
    /**
     * Update the password strength meter
     * @param {number} strength 
     */
    function updatePasswordStrengthMeter(strength) {
        if (!passwordStrengthMeter) return;
        
        // Remove existing classes
        passwordStrengthMeter.className = 'password-strength-meter mt-2';
        
        // Add new class based on strength
        let strengthClass = '';
        let strengthText = '';
        
        switch (strength) {
            case 0:
                strengthClass = 'bg-danger';
                strengthText = 'Very Weak';
                break;
            case 1:
                strengthClass = 'bg-warning';
                strengthText = 'Weak';
                break;
            case 2:
                strengthClass = 'bg-info';
                strengthText = 'Medium';
                break;
            case 3:
                strengthClass = 'bg-primary';
                strengthText = 'Strong';
                break;
            case 4:
                strengthClass = 'bg-success';
                strengthText = 'Very Strong';
                break;
            default:
                strengthClass = 'bg-secondary';
                strengthText = '';
        }
        
        // Update the meter
        passwordStrengthMeter.classList.add(strengthClass);
        passwordStrengthMeter.style.width = (strength * 25) + '%';
        passwordStrengthMeter.style.height = '6px';
        passwordStrengthMeter.style.display = 'block';
        passwordStrengthMeter.style.transition = 'width 0.3s ease-in-out';
        passwordStrengthMeter.title = strengthText;
    }
});
