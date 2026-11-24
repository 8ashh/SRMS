from functools import wraps
from flask import Blueprint, render_template, request, redirect, url_for, flash, session, g
from extensions import db
from models import User, Student
from services.audit_service import AuditService

auth_bp = Blueprint('auth', __name__)

def get_current_user():
    """Helper to fetch currently logged in user model or None."""
    user_id = session.get('user_id')
    if user_id:
        return User.query.get(user_id)
    return None

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash("Please sign in to access this page.", "warning")
            return redirect(url_for('auth.login', next=request.path))
        return f(*args, **kwargs)
    return decorated_function

def role_required(allowed_roles):
    """Decorator ensuring current user has one of the allowed roles."""
    if isinstance(allowed_roles, str):
        allowed_roles = [allowed_roles]

    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if 'user_id' not in session:
                flash("Please sign in first.", "warning")
                return redirect(url_for('auth.login'))
            user_role = session.get('role')
            if user_role not in allowed_roles:
                flash("Access denied: You do not have permission to view this resource.", "danger")
                # Redirect to appropriate home page based on role
                if user_role == 'admin':
                    return redirect(url_for('admin.dashboard'))
                elif user_role == 'faculty':
                    return redirect(url_for('faculty.dashboard'))
                elif user_role == 'student':
                    return redirect(url_for('student.dashboard'))
                return redirect(url_for('auth.login'))
            return f(*args, **kwargs)
        return decorated_function
    return decorator


@auth_bp.route('/', methods=['GET'])
def index():
    """Landing route: redirect to dashboard if logged in, else to login page."""
    if 'user_id' in session:
        role = session.get('role')
        if role == 'admin':
            return redirect(url_for('admin.dashboard'))
        elif role == 'faculty':
            return redirect(url_for('faculty.dashboard'))
        elif role == 'student':
            return redirect(url_for('student.dashboard'))
    return redirect(url_for('auth.login'))


@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if 'user_id' in session:
        role = session.get('role')
        if role == 'admin':
            return redirect(url_for('admin.dashboard'))
        elif role == 'faculty':
            return redirect(url_for('faculty.dashboard'))
        elif role == 'student':
            return redirect(url_for('student.dashboard'))

    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '').strip()

        if not username or not password:
            flash("Please enter both username and password.", "danger")
            return render_template('login.html', username=username)

        user = User.query.filter_by(username=username).first()

        if user and user.check_password(password):
            session.clear()
            session['user_id'] = user.user_id
            session['username'] = user.username
            session['role'] = user.role
            session['faculty_name'] = user.faculty_name
            session['student_id'] = user.student_id

            AuditService.log(
                action="LOGIN_SUCCESS",
                module="Authentication",
                record_id=user.user_id,
                description=f"User '{user.username}' logged in successfully as {user.role}."
            )

            flash(f"Welcome back, {user.faculty_name or user.username}!", "success")

            next_url = request.args.get('next')
            if next_url and next_url.startswith('/'):
                return redirect(next_url)

            if user.role == 'admin':
                return redirect(url_for('admin.dashboard'))
            elif user.role == 'faculty':
                return redirect(url_for('faculty.dashboard'))
            elif user.role == 'student':
                return redirect(url_for('student.dashboard'))
            return redirect(url_for('auth.login'))
        else:
            AuditService.log(
                action="LOGIN_FAILURE",
                module="Authentication",
                description=f"Failed login attempt for username '{username}'."
            )
            flash("Invalid username or password. Please verify your credentials.", "danger")

    return render_template('login.html')


@auth_bp.route('/logout', methods=['GET', 'POST'])
def logout():
    username = session.get('username', 'Unknown')
    AuditService.log(
        action="LOGOUT",
        module="Authentication",
        description=f"User '{username}' logged out."
    )
    session.clear()
    flash("You have been successfully logged out.", "info")
    return redirect(url_for('auth.login'))
