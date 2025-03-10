"""
Firebase configuration for OCR A-Level Computer Science AI Tutor
"""
import os
import firebase_admin
from firebase_admin import credentials, auth
import pyrebase

class FirebaseConfig:
    """Firebase configuration class"""
    
    def __init__(self, app=None):
        """Initialize Firebase configuration"""
        self.app = app
        self.firebase_admin_app = None
        self.pyrebase_app = None
        self.auth = None
        self.db = None
        self.storage = None
        
        # Firebase configuration
        self.config = {
            "apiKey": os.environ.get("FIREBASE_API_KEY"),
            "authDomain": os.environ.get("FIREBASE_AUTH_DOMAIN"),
            "projectId": os.environ.get("FIREBASE_PROJECT_ID"),
            "storageBucket": os.environ.get("FIREBASE_STORAGE_BUCKET"),
            "messagingSenderId": os.environ.get("FIREBASE_MESSAGING_SENDER_ID"),
            "appId": os.environ.get("FIREBASE_APP_ID"),
            "measurementId": os.environ.get("FIREBASE_MEASUREMENT_ID"),
            "databaseURL": f"https://{os.environ.get('FIREBASE_PROJECT_ID')}.firebaseio.com"
        }
        
        # Service account path
        self.service_account_path = os.environ.get("FIREBASE_SERVICE_ACCOUNT_PATH")
        
    def init_app(self, app):
        """Initialize Firebase with Flask app"""
        self.app = app
        
        try:
            # Initialize Firebase Admin SDK
            if not firebase_admin._apps:
                app.logger.info(f"Initializing Firebase Admin SDK with service account: {self.service_account_path}")
                
                try:
                    if self.service_account_path and os.path.exists(self.service_account_path):
                        app.logger.info(f"Using service account file from path: {self.service_account_path}")
                        cred = credentials.Certificate(self.service_account_path)
                    else:
                        app.logger.warning(f"Service account file not found at {self.service_account_path}, checking fallback locations")
                        
                        # Try fallback locations in Elastic Beanstalk environment
                        eb_fallback_path = "/var/app/current/credentials/firebase-service-account.json"
                        if os.path.exists(eb_fallback_path):
                            app.logger.info(f"Using service account from EB fallback location: {eb_fallback_path}")
                            cred = credentials.Certificate(eb_fallback_path)
                        else:
                            app.logger.warning("No service account found, using application default credentials")
                            cred = credentials.ApplicationDefault()
                    
                    app.logger.info("Initializing Firebase Admin app")
                    self.firebase_admin_app = firebase_admin.initialize_app(cred, {
                        'projectId': self.config['projectId'],
                        'storageBucket': self.config['storageBucket']
                    })
                    app.logger.info("Firebase Admin SDK initialized successfully")
                except Exception as e:
                    app.logger.error(f"Error initializing Firebase Admin SDK: {e}")
                    # Continue without firebase admin in case of error
                    self.firebase_admin_app = None
            else:
                app.logger.info("Firebase Admin app already initialized, getting existing app")
                self.firebase_admin_app = firebase_admin.get_app()
            
            # Initialize Pyrebase
            app.logger.info("Initializing Pyrebase")
            self.pyrebase_app = pyrebase.initialize_app(self.config)
            self.auth = self.pyrebase_app.auth()
            self.db = self.pyrebase_app.database()
            self.storage = self.pyrebase_app.storage()
            app.logger.info("Pyrebase initialized successfully")
            
        except Exception as e:
            app.logger.error(f"Error in Firebase initialization: {e}")
            # Set to None to handle gracefully in the app
            self.pyrebase_app = None
            self.auth = None
            self.db = None
            self.storage = None
        
        # Add Firebase to Flask app context
        app.extensions['firebase'] = self
        app.logger.info("Firebase configuration added to Flask app context")
        
        return self
    
    def verify_id_token(self, id_token):
        """Verify Firebase ID token"""
        try:
            return auth.verify_id_token(id_token)
        except Exception as e:
            app.logger.error(f"Error verifying Firebase ID token: {e}")
            return None
    
    def get_user(self, uid):
        """Get user by UID"""
        try:
            return auth.get_user(uid)
        except Exception as e:
            app.logger.error(f"Error getting Firebase user: {e}")
            return None
    
    def create_user(self, email, password, display_name=None):
        """Create a new Firebase user"""
        try:
            user_data = {
                'email': email,
                'password': password,
                'email_verified': False
            }
            
            if display_name:
                user_data['display_name'] = display_name
                
            return auth.create_user(**user_data)
        except Exception as e:
            app.logger.error(f"Error creating Firebase user: {e}")
            return None
    
    def update_user(self, uid, **kwargs):
        """Update a Firebase user"""
        try:
            return auth.update_user(uid, **kwargs)
        except Exception as e:
            app.logger.error(f"Error updating Firebase user: {e}")
            return None
    
    def delete_user(self, uid):
        """Delete a Firebase user"""
        try:
            return auth.delete_user(uid)
        except Exception as e:
            app.logger.error(f"Error deleting Firebase user: {e}")
            return None
    
    def send_password_reset_email(self, email):
        """Send password reset email"""
        try:
            return self.auth.send_password_reset_email(email)
        except Exception as e:
            app.logger.error(f"Error sending password reset email: {e}")
            return None
    
    def sign_in_with_email_and_password(self, email, password):
        """Sign in with email and password"""
        try:
            return self.auth.sign_in_with_email_and_password(email, password)
        except Exception as e:
            app.logger.error(f"Error signing in with email and password: {e}")
            return None
    
    def refresh_token(self, refresh_token):
        """Refresh Firebase ID token"""
        try:
            return self.auth.refresh(refresh_token)
        except Exception as e:
            app.logger.error(f"Error refreshing Firebase token: {e}")
            return None

# Create Firebase configuration instance
firebase = FirebaseConfig()
