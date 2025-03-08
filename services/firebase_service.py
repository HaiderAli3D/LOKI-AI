"""
Firebase service for OCR A-Level Computer Science AI Tutor
"""
from flask import current_app, g
from config.firebase_config import firebase

class FirebaseService:
    """Firebase service class"""
    
    @staticmethod
    def get_firebase():
        """Get Firebase instance"""
        if 'firebase' not in g:
            g.firebase = firebase
        return g.firebase
    
    @staticmethod
    def create_user(email, password, first_name=None, last_name=None):
        """Create a new Firebase user"""
        firebase_instance = FirebaseService.get_firebase()
        
        # Create display name from first and last name
        display_name = None
        if first_name and last_name:
            display_name = f"{first_name} {last_name}"
        elif first_name:
            display_name = first_name
        
        # Create user in Firebase
        firebase_user = firebase_instance.create_user(email, password, display_name)
        
        if not firebase_user:
            return None
        
        return {
            'uid': firebase_user.uid,
            'email': firebase_user.email,
            'display_name': firebase_user.display_name
        }
    
    @staticmethod
    def get_user(uid):
        """Get user by UID"""
        firebase_instance = FirebaseService.get_firebase()
        firebase_user = firebase_instance.get_user(uid)
        
        if not firebase_user:
            return None
        
        return {
            'uid': firebase_user.uid,
            'email': firebase_user.email,
            'display_name': firebase_user.display_name,
            'email_verified': firebase_user.email_verified
        }
    
    @staticmethod
    def update_user(uid, **kwargs):
        """Update a Firebase user"""
        firebase_instance = FirebaseService.get_firebase()
        firebase_user = firebase_instance.update_user(uid, **kwargs)
        
        if not firebase_user:
            return None
        
        return {
            'uid': firebase_user.uid,
            'email': firebase_user.email,
            'display_name': firebase_user.display_name
        }
    
    @staticmethod
    def delete_user(uid):
        """Delete a Firebase user"""
        firebase_instance = FirebaseService.get_firebase()
        return firebase_instance.delete_user(uid)
    
    @staticmethod
    def verify_id_token(id_token):
        """Verify Firebase ID token"""
        firebase_instance = FirebaseService.get_firebase()
        return firebase_instance.verify_id_token(id_token)
    
    @staticmethod
    def sign_in_with_email_and_password(email, password):
        """Sign in with email and password"""
        firebase_instance = FirebaseService.get_firebase()
        return firebase_instance.sign_in_with_email_and_password(email, password)
    
    @staticmethod
    def refresh_token(refresh_token):
        """Refresh Firebase ID token"""
        firebase_instance = FirebaseService.get_firebase()
        return firebase_instance.refresh_token(refresh_token)
    
    @staticmethod
    def send_password_reset_email(email):
        """Send password reset email"""
        firebase_instance = FirebaseService.get_firebase()
        return firebase_instance.send_password_reset_email(email)
    
    @staticmethod
    def get_user_by_email(email):
        """Get user by email"""
        try:
            from firebase_admin import auth
            return auth.get_user_by_email(email)
        except Exception as e:
            current_app.logger.error(f"Error getting Firebase user by email: {e}")
            return None
