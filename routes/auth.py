"""
Authentication routes for OCR A-Level Computer Science AI Tutor
"""
from flask import render_template, redirect, url_for, request, flash, session, jsonify, current_app
from flask_login import login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from routes import auth_bp
from models.user import User
from services.firebase_service import FirebaseService
from config.database_config import db
from datetime import datetime

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    """Login page"""
    if current_user.is_authenticated:
        if current_user.is_admin():
            return redirect(url_for('admin.dashboard'))
        return redirect(url_for('student.dashboard'))
    
    # Get the role from the URL parameter
    role = request.args.get('role', 'student')
    is_admin_login = role == 'admin'
    
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        remember = 'remember' in request.form
        user_role = request.form.get('role', 'student')  # Get role from form
        
        # Find user by email
        user = User.query.filter_by(email=email).first()
        
        if user and user.check_password(password):
            # Check if user role matches requested role
            is_admin = user.is_admin()
            
            if (user_role == 'admin' and not is_admin):
                flash('You do not have admin privileges', 'danger')
                return render_template('auth/login.html', is_admin_login=is_admin_login)
            
            # Update last login
            user.update_last_login()
            
            # Login user
            login_user(user, remember=remember)
            
            # Redirect to next page or dashboard
            next_page = request.args.get('next')
            if next_page:
                return redirect(next_page)
            
            if user.is_admin():
                return redirect(url_for('admin.dashboard'))
            else:
                return redirect(url_for('student.dashboard'))
        
        # Try Firebase login if user not found or password incorrect
        try:
            firebase_user = FirebaseService.sign_in_with_email_and_password(email, password)
            
            if firebase_user:
                # Get user info
                user_info = firebase_user.get('idToken')
                
                if user_info:
                    # Verify token
                    decoded_token = FirebaseService.verify_id_token(user_info)
                    
                    if decoded_token:
                        # Get or create user
                        user = User.query.filter_by(email=email).first()
                        
                        if not user:
                            # Create user
                            user = User(
                                email=email,
                                first_name=decoded_token.get('name', '').split(' ')[0] if decoded_token.get('name') else '',
                                last_name=decoded_token.get('name', '').split(' ')[-1] if decoded_token.get('name') else '',
                                firebase_uid=decoded_token.get('uid')
                            )
                            db.session.add(user)
                            db.session.commit()
                        
                        # Update last login
                        user.update_last_login()
                        
                        # Login user
                        login_user(user, remember=remember)
                        
                        # Check if user role matches requested role
                        is_admin = user.is_admin()
                        
                        if (user_role == 'admin' and not is_admin):
                            flash('You do not have admin privileges', 'danger')
                            return render_template('auth/login.html', is_admin_login=is_admin_login)
                        
                        # Redirect to next page or dashboard
                        next_page = request.args.get('next')
                        if next_page:
                            return redirect(next_page)
                        
                        if user.is_admin():
                            return redirect(url_for('admin.dashboard'))
                        else:
                            return redirect(url_for('student.dashboard'))
        except Exception as e:
            current_app.logger.error(f"Firebase login error: {e}")
        
        flash('Invalid email or password', 'danger')
    
    return render_template('auth/login.html', is_admin_login=is_admin_login)

@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    """Register page"""
    if current_user.is_authenticated:
        return redirect(url_for('student.dashboard'))
    
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        confirm_password = request.form.get('confirm_password')
        first_name = request.form.get('first_name')
        last_name = request.form.get('last_name')
        terms = 'terms' in request.form
        
        # Check if passwords match
        if password != confirm_password:
            flash('Passwords do not match', 'danger')
            return render_template('auth/register.html')
        
        # Check if terms are accepted
        if not terms:
            flash('You must accept the terms and conditions', 'danger')
            return render_template('auth/register.html')
        
        # Check if user already exists
        user = User.query.filter_by(email=email).first()
        if user:
            flash('Email already registered', 'danger')
            return render_template('auth/register.html')
        
        # Create user in Firebase
        try:
            firebase_user = FirebaseService.create_user(email, password, first_name, last_name)
            
            if firebase_user:
                # Create user in database
                user = User(
                    email=email,
                    first_name=first_name,
                    last_name=last_name,
                    firebase_uid=firebase_user.get('uid')
                )
                db.session.add(user)
                db.session.commit()
                
                # Login user
                login_user(user)
                
                # Redirect to subscription plans
                return redirect(url_for('subscription.plans'))
            
        except Exception as e:
            current_app.logger.error(f"Firebase registration error: {e}")
            flash('Error creating account', 'danger')
            return render_template('auth/register.html')
        
        # Create user in database with password hash
        user = User(
            email=email,
            first_name=first_name,
            last_name=last_name
        )
        user.set_password(password)
        
        db.session.add(user)
        db.session.commit()
        
        # Login user
        login_user(user)
        
        # Redirect to subscription plans
        return redirect(url_for('subscription.plans'))
    
    return render_template('auth/register.html')

@auth_bp.route('/logout')
@login_required
def logout():
    """Logout user"""
    logout_user()
    return redirect(url_for('main.index'))

@auth_bp.route('/profile', methods=['GET', 'POST'])
@login_required
def profile():
    """User profile page"""
    if request.method == 'POST':
        first_name = request.form.get('first_name')
        last_name = request.form.get('last_name')
        
        # Update user
        current_user.first_name = first_name
        current_user.last_name = last_name
        
        db.session.commit()
        
        # Update Firebase user if connected
        if current_user.firebase_uid:
            try:
                display_name = f"{first_name} {last_name}"
                FirebaseService.update_user(current_user.firebase_uid, display_name=display_name)
            except Exception as e:
                current_app.logger.error(f"Firebase update error: {e}")
        
        flash('Profile updated', 'success')
        return redirect(url_for('auth.profile'))
    
    # Get recent sessions
    recent_sessions = current_user.get_recent_sessions()
    
    return render_template('auth/profile.html', user=current_user, recent_sessions=recent_sessions)

@auth_bp.route('/reset-password', methods=['GET', 'POST'])
def reset_password():
    """Reset password page"""
    if current_user.is_authenticated:
        return redirect(url_for('student.dashboard'))
    
    if request.method == 'POST':
        email = request.form.get('email')
        
        # Send password reset email
        try:
            FirebaseService.send_password_reset_email(email)
            flash('Password reset email sent', 'success')
            return redirect(url_for('auth.login'))
        except Exception as e:
            current_app.logger.error(f"Firebase password reset error: {e}")
            flash('Error sending password reset email', 'danger')
    
    return render_template('auth/reset_password.html')

@auth_bp.route('/firebase-token', methods=['POST'])
def firebase_token():
    """Handle Firebase token"""
    data = request.get_json()
    
    if not data or 'token' not in data:
        return jsonify({'error': 'No token provided'}), 400
    
    token = data['token']
    
    try:
        # Verify token
        decoded_token = FirebaseService.verify_id_token(token)
        
        if not decoded_token:
            return jsonify({'error': 'Invalid token'}), 401
        
        # Get user info
        uid = decoded_token.get('uid')
        email = decoded_token.get('email')
        name = decoded_token.get('name', '')
        
        if not email:
            return jsonify({'error': 'No email in token'}), 400
        
        # Get or create user
        user = User.query.filter_by(email=email).first()
        
        if not user:
            # Split name into first and last name
            name_parts = name.split(' ')
            first_name = name_parts[0] if name_parts else ''
            last_name = name_parts[-1] if len(name_parts) > 1 else ''
            
            # Create user
            user = User(
                email=email,
                first_name=first_name,
                last_name=last_name,
                firebase_uid=uid
            )
            db.session.add(user)
            db.session.commit()
        
        # Update last login
        user.update_last_login()
        
        # Login user
        login_user(user)
        
        return jsonify({
            'success': True,
            'user': user.to_dict(),
            'redirect': url_for('student.dashboard') if not user.is_admin() else url_for('admin.dashboard')
        })
        
    except Exception as e:
        current_app.logger.error(f"Firebase token error: {e}")
        return jsonify({'error': str(e)}), 500
