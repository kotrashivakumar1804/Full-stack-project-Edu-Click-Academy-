from functools import wraps
from flask import redirect, url_for, flash, session
from flask_login import current_user

def student_required(f):
    """Enforces that the current logged-in user has a student role."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or session.get('role') != 'student':
            flash('Please log in as a student to access this page.', 'warning')
            return redirect(url_for('auth.login'))
        return f(*args, **kwargs)
    return decorated_function

def admin_required(f):
    """Enforces that the current logged-in user has an admin role."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or session.get('role') != 'admin':
            flash('Administrator access required. Please log in.', 'danger')
            return redirect(url_for('auth.admin_login'))
        return f(*args, **kwargs)
    return decorated_function
