from flask import Blueprint, render_template, redirect, url_for, flash, session, request
from flask_login import login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from app.extensions import db
from app.models.student import Student
from app.models.admin import Admin
from app.models.notification import Notification
from app.forms.auth import StudentRegistrationForm, StudentLoginForm, AdminLoginForm, ForgotPasswordForm, ResetPasswordForm

auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        if session.get('role') == 'admin':
            return redirect(url_for('admin.dashboard'))
        return redirect(url_for('student.dashboard'))
        
    form = StudentRegistrationForm()
    if form.validate_on_submit():
        hashed_password = generate_password_hash(form.password.data)
        student = Student(
            full_name=form.full_name.data,
            email=form.email.data.lower(),
            mobile=form.mobile.data,
            password=hashed_password,
            gender=form.gender.data
        )
        db.session.add(student)
        db.session.commit()
        
        # Add welcome notification
        welcome_notif = Notification(
            student_id=student.student_id,
            title="Welcome to Portal!",
            message=f"Hi {student.full_name}, thank you for registering with us. Browse our courses and contact the admin/instructor to enroll!"
        )
        db.session.add(welcome_notif)
        db.session.commit()
        
        flash('Registration successful! You can now log in.', 'success')
        return redirect(url_for('auth.login'))
        
    return render_template('auth/register.html', form=form)


@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        if session.get('role') == 'admin':
            return redirect(url_for('admin.dashboard'))
        return redirect(url_for('student.dashboard'))
        
    form = StudentLoginForm()
    if form.validate_on_submit():
        student = Student.query.filter_by(email=form.email.data.lower()).first()
        if student and check_password_hash(student.password, form.password.data):
            from datetime import datetime
            student.last_login = datetime.utcnow()
            student.login_count = (student.login_count or 0) + 1
            db.session.commit()
            
            session['role'] = 'student'
            login_user(student, remember=form.remember_me.data)
            flash(f'Welcome back, {student.full_name}!', 'success')
            next_page = request.args.get('next')
            return redirect(next_page) if next_page else redirect(url_for('student.dashboard'))
        else:
            flash('Invalid email or password.', 'danger')
            
    return render_template('auth/login.html', form=form)


@auth_bp.route('/admin/login', methods=['GET', 'POST'])
def admin_login():
    if current_user.is_authenticated:
        if session.get('role') == 'admin':
            return redirect(url_for('admin.dashboard'))
        return redirect(url_for('student.dashboard'))
        
    form = AdminLoginForm()
    if form.validate_on_submit():
        admin = Admin.query.filter_by(email=form.email.data.lower()).first()
        if admin and check_password_hash(admin.password, form.password.data):
            session['role'] = 'admin'
            login_user(admin)
            flash('Secure Administrator Login Successful.', 'success')
            next_page = request.args.get('next')
            return redirect(next_page) if next_page else redirect(url_for('admin.dashboard'))
        else:
            flash('Invalid admin credentials.', 'danger')
            
    return render_template('auth/admin_login.html', form=form)


@auth_bp.route('/forgot-password', methods=['GET', 'POST'])
def forgot_password():
    form = ForgotPasswordForm()
    if form.validate_on_submit():
        email = form.email.data.lower()
        # Find user
        student = Student.query.filter_by(email=email).first()
        if student:
            # In a real app we'd email a token. We will mock it here.
            print(f"[MOCK EMAIL] Password reset requested for student: {student.full_name} ({email})")
            print(f"[MOCK EMAIL] Reset Link: http://localhost:5000/reset-password-mock?email={email}")
            flash('A password reset link has been sent to your email address (simulated in console).', 'info')
        else:
            # Don't leak accounts, pretend we sent it
            flash('If that email is registered, password reset instructions have been sent.', 'info')
        return redirect(url_for('auth.login'))
        
    return render_template('auth/forgot_password.html', form=form)


@auth_bp.route('/logout')
@login_required
def logout():
    from datetime import datetime
    role = session.get('role')
    if role == 'student' and current_user.is_authenticated:
        current_user.last_logout = datetime.utcnow()
        db.session.commit()
    logout_user()
    session.pop('role', None)
    flash('You have logged out successfully.', 'success')
    return redirect(url_for('main.home'))


@auth_bp.route('/reset-password-mock', methods=['GET', 'POST'])
def reset_password_mock():
    email = request.args.get('email', '').lower()
    student = Student.query.filter_by(email=email).first_or_404()
    
    form = ResetPasswordForm()
    if form.validate_on_submit():
        student.password = generate_password_hash(form.password.data)
        
        # Send Notification
        notif = Notification(
            student_id=student.student_id,
            title="Password Reset Successful",
            message="Your account password has been successfully reset using the recovery link."
        )
        db.session.add(notif)
        db.session.commit()
        
        flash('Your password has been reset successfully! You can now log in.', 'success')
        return redirect(url_for('auth.login'))
        
    return render_template('auth/reset_password.html', form=form, email=email)

