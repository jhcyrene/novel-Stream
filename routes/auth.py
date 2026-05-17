from flask import Blueprint, render_template, redirect, url_for, session, flash, request
from forms.auth_forms import LoginForm, RegistrationForm
from models import Novel, User
from extensions import db

# Create the Blueprint
auth_bp = Blueprint('auth', __name__)

# -----login-----
@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()

    if form.validate_on_submit():
        user_email = form.email.data 
        user_password = form.password.data

        # Find the user by email
        user = User.query.filter_by(email=user_email).first()
        
        # Verify credentials
        if user and user.verify_password(user_password):
            # Set session variables
            session['username'] = user.username 
            session['user_id'] = user.id
            session['avatar_url'] = user.avatar_url
            
            # Check if user is admin
            if user.is_admin:
                session['is_admin'] = True
                flash(f'Admin login successful! Welcome back, {user.username}.', 'success')
                return redirect(url_for('admin.dashboard'))
            else:
                flash(f'Login successful! Welcome back, {user.username}.', 'success')
                return redirect(url_for('main.home'))
        else:
            flash('Invalid email or password. Please try again.', 'error')
            
    return render_template('login.html', form=form)


# -----register-----
@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    form = RegistrationForm()
    
    if form.validate_on_submit():    
        user_name = form.name.data
        user_email = form.email.data
        user_password = form.password.data

        # Check if user already exists
        existing_user = User.query.filter_by(email=user_email).first()
        
        if existing_user is None: 
            new_user = User(
                username=user_name,
                email=user_email,
                password=user_password
            )
            
            # Save to database
            db.session.add(new_user)
            db.session.commit()
            
            flash(f'Account created successfully for {user_name}! Please log in.', 'success')
            return redirect(url_for('auth.login')) 
        else:    
            flash('That email address is already registered. Please log in instead.', 'error')
            
    return render_template('register.html', form=form, active_page='register')


@auth_bp.route('/logout')
def logout():
    if 'username' in session:
        username = session['username']
        
        # Clear all session data
        session.clear()
        
        flash(f'You have successfully logged out, {username}. Come back soon!', 'success')
    return redirect(url_for('main.home'))