from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask import session # Import session to check for admin status
from models import Novel, User # Assuming you have these models
from extensions import db # Database instance
from forms.forms import NovelForm # Import the form for adding/editing novels

admin_bp = Blueprint('admin', __name__, url_prefix='/admin')

def admin_required(f):
    def decorated_function(*args, **kwargs):
        user_id = session.get('user_id')
    
        if not user_id:
            flash('Please log in to access the admin panel.', 'info')
            return redirect(url_for('auth.login'))
        
        user = User.query.get(user_id)
        if not user or not user.is_admin:
            flash('Access Denied: Administrator privileges required.', 'warning')
            return redirect(url_for('main.home')) 
            
        return f(*args, **kwargs)
        
    decorated_function.__name__ = f.__name__
    return decorated_function

@admin_bp.route('/AdminDashboard') 
@admin_required
def dashboard():
    return render_template('admin/dashboard.html', active_page='admin_dashboard')

# ----------------------------------------------------------------------
# NOVEL MANAGEMENT
# ----------------------------------------------------------------------

# 1. READ/LIST ALL NOVELS
@admin_bp.route('/novels')
@admin_required
def manage_novels():
    novels = Novel.query.all()
    return render_template('admin/manage_novels.html', novels=novels)


# 3. UPDATE/EDIT NOVEL
@admin_bp.route('/novels/edit/<int:novel_id>', methods=['GET', 'POST'])
@admin_required
def edit_novel(novel_id):
    novel = Novel.query.get_or_404(novel_id)
    
    if request.method == 'POST':
        novel.title = request.form.get('title')
        # ... update other fields ...
        db.session.commit()
        flash(f'Novel "{novel.title}" updated successfully!', 'success')
        return redirect(url_for('.manage_novels'))
        
    return render_template('admin/edit_novel.html', novel=novel)

# 4. DELETE NOVEL
@admin_bp.route('/novels/delete/<int:novel_id>', methods=['POST'])
@admin_required
def delete_novel(novel_id):
    novel = Novel.query.get_or_404(novel_id)
    title = novel.title
    
    db.session.delete(novel)
    db.session.commit()
    flash(f'Novel "{title}" deleted successfully.', 'success')
    return redirect(url_for('.manage_novels'))


# ----------------------------------------------------------------------
# USER MANAGEMENT (similar CRUD structure)
# ----------------------------------------------------------------------

# 1. READ/LIST ALL USERS
@admin_bp.route('/users')
@admin_required
def manage_users():
    users = User.query.all()
    return render_template('admin/manage_users.html', users=users)

# 2. UPDATE/EDIT USER (e.g., changing role or status)
@admin_bp.route('/users/edit/<int:user_id>', methods=['GET', 'POST'])
@admin_required
def edit_user(user_id):
    user = User.query.get_or_404(user_id)
    
    if request.method == 'POST':
        # Example: Update user role/status
        user.is_admin = bool(request.form.get('is_admin')) 
        db.session.commit()
        flash(f'User "{user.username}" updated.', 'success')
        return redirect(url_for('.manage_users'))
        
    return render_template('admin/edit_user.html', user=user)

# 3. DELETE USER
@admin_bp.route('/users/delete/<int:user_id>', methods=['POST'])
@admin_required
def delete_user(user_id):
    user = User.query.get_or_404(user_id)
    username = user.username
    
    db.session.delete(user)
    db.session.commit()
    flash(f'User "{username}" deleted successfully.', 'success')
    return redirect(url_for('.manage_users'))

@admin_bp.route('/Adminlogin', methods=['GET', 'POST'], endpoint='admin_login')
def admin_login():
    # Note: LoginForm should be imported and available
    from forms.auth_forms import LoginForm 
    form = LoginForm(request.form) # Use request.form to initialize the form

    if request.method == 'POST' and form.validate():
        user_email = form.email.data 
        user_password = form.password.data

        user = User.query.filter_by(email=user_email).first()
        
        if user and user.verify_password(user_password) and user.is_admin:
            
            # Successful Admin Login
            session['user_id'] = user.id
            session['username'] = user.username
            session['is_admin'] = True # The critical admin flag
            
            flash(f'Admin Login Successful! Welcome, {user.username}.', 'success')
            
            # Redirect to the main admin dashboard (which is now just '.dashboard')
            return redirect(url_for('.dashboard')) 
        
        else:
            flash('Invalid Credentials or Insufficient Privileges.', 'error')
            
    return render_template('admin/admin_login.html', form=form) # Changed template path for consistency