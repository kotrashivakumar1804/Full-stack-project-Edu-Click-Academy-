import os
from datetime import datetime
from flask import Blueprint, render_template, redirect, url_for, flash, request, current_app, session
from flask_login import login_required, current_user
from werkzeug.utils import secure_filename
from werkzeug.security import generate_password_hash, check_password_hash
from app.extensions import db
from app.models.student import Student
from app.models.course import Course
from app.models.enrollment import Enrollment
from app.models.message import ContactMessage
from app.models.announcement import Announcement
from datetime import datetime as dt
from app.models.notification import Notification
from app.models.inquiry import Inquiry, InquiryReply
from app.forms.student import EditProfileForm, ChangePasswordForm
from app.forms.contact import CourseInquiryForm, InquiryCreateForm
from app.utils.decorators import student_required

student_bp = Blueprint('student', __name__, url_prefix='/student')

def get_profile_completion(student):
    """Calculates student profile completion percentage."""
    score = 0
    if student.full_name: score += 20
    if student.email: score += 20
    if student.mobile: score += 20
    if student.gender: score += 15
    if student.profile_picture and student.profile_picture != 'default_profile.png': 
        score += 25
    else:
        score += 10  # partial credit for default picture
    return min(score, 100)


@student_bp.route('/dashboard')
@login_required
@student_required
def dashboard():
    # Gather statistics
    total_available_courses = Course.query.filter_by(status='Active').count()
    my_enrollments = Enrollment.query.filter_by(student_id=current_user.student_id).all()
    my_courses_count = len([e for e in my_enrollments if e.enrollment_status == 'Approved'])
    
    # Announcements
    latest_announcements = Announcement.query.order_by(Announcement.created_at.desc()).limit(3).all()
    
    # Profile status
    completion = get_profile_completion(current_user)
    
    # Notifications
    unread_notifications = Notification.query.filter_by(
        student_id=current_user.student_id, is_read=False
    ).order_by(Notification.created_at.desc()).limit(5).all()
    
    return render_template('student/dashboard.html',
                           total_available_courses=total_available_courses,
                           my_courses_count=my_courses_count,
                           my_enrollments_count=len(my_enrollments),
                           latest_announcements=latest_announcements,
                           profile_completion=completion,
                           notifications=unread_notifications)


@student_bp.route('/profile')
@login_required
@student_required
def profile():
    completion = get_profile_completion(current_user)
    return render_template('student/profile.html', profile_completion=completion)


@student_bp.route('/profile/edit', methods=['GET', 'POST'])
@login_required
@student_required
def edit_profile():
    form = EditProfileForm(obj=current_user)
    if form.validate_on_submit():
        current_user.full_name = form.full_name.data
        current_user.email = form.email.data.lower()
        current_user.mobile = form.mobile.data
        current_user.gender = form.gender.data
        
        # Handle file upload
        file = form.profile_picture.data
        if file:
            filename = secure_filename(file.filename)
            unique_filename = f"student_{current_user.student_id}_{int(datetime.utcnow().timestamp())}_{filename}"
            upload_dir = os.path.join(current_app.config['UPLOAD_FOLDER'], 'profiles')
            
            # Ensure upload folder exists
            os.makedirs(upload_dir, exist_ok=True)
            
            file_path = os.path.join(upload_dir, unique_filename)
            file.save(file_path)
            current_user.profile_picture = f"uploads/profiles/{unique_filename}"
            
        db.session.commit()
        flash('Your profile has been updated successfully!', 'success')
        return redirect(url_for('student.profile'))
        
    return render_template('student/edit_profile.html', form=form)


@student_bp.route('/profile/change-password', methods=['GET', 'POST'])
@login_required
@student_required
def change_password():
    form = ChangePasswordForm()
    if form.validate_on_submit():
        if check_password_hash(current_user.password, form.current_password.data):
            current_user.password = generate_password_hash(form.new_password.data)
            
            # Send Notification
            notif = Notification(
                student_id=current_user.student_id,
                title="Password Changed",
                message="Your account password was updated successfully. If you did not initiate this change, contact admin support immediately."
            )
            db.session.add(notif)
            db.session.commit()
            
            flash('Your password has been changed successfully.', 'success')
            return redirect(url_for('student.profile'))
        else:
            flash('Incorrect current password.', 'danger')
            
    return render_template('student/change_password.html', form=form)


@student_bp.route('/courses')
@login_required
@student_required
def courses():
    enrollments = Enrollment.query.filter_by(student_id=current_user.student_id).all()
    return render_template('student/courses.html', enrollments=enrollments)


@student_bp.route('/courses/<int:course_id>/contact', methods=['GET', 'POST'])
@login_required
@student_required
def contact_instructor(course_id):
    course = Course.query.get_or_404(course_id)
    if course.status != 'Active':
        flash('This course is not available.', 'danger')
        return redirect(url_for('main.courses'))
        
    # Check if student is already enrolled
    existing_enrollment = Enrollment.query.filter_by(
        student_id=current_user.student_id, course_id=course_id
    ).first()
    
    if existing_enrollment and existing_enrollment.enrollment_status in ['Approved', 'Payment Submitted']:
        flash('You have already requested enrollment or are active in this course.', 'info')
        return redirect(url_for('student.courses'))
    
    # Detect any active discount offer announcement using course properties
    price_details = course.current_price_details
    active_offer = price_details['offer']
    
    # Calculate discounted fee
    original_fee = price_details['original_fee']
    discounted_fee = price_details['discounted_fee']
    discount_amount = price_details['discount_amount']

    form = CourseInquiryForm()
    if request.method == 'POST':
        action = request.form.get('action')
        
        # Branch 1: General Inquiry Message
        if action == 'inquiry':
            if form.validate_on_submit():
                subject = f"Course Inquiry: {course.course_name} (Student ID: {current_user.student_id})"
                inquiry = ContactMessage(
                    name=current_user.full_name,
                    email=current_user.email,
                    subject=subject,
                    message=form.message.data
                )
                db.session.add(inquiry)
                db.session.commit()
                flash('Your inquiry has been sent to the instructor. You can check responses in the "My Inquiries" section.', 'success')
                return redirect(url_for('student.inquiries'))
                
        # Branch 2: Secure Payment & Enrollment
        elif action == 'enroll':
            txn_ref = request.form.get('txn_reference', '').strip()
            file = request.files.get('payment_screenshot')
            
            if not txn_ref or not file:
                flash('Please provide both the Transaction Reference ID and the Payment Receipt Screenshot.', 'danger')
                return redirect(url_for('student.contact_instructor', course_id=course_id))
            
            # Re-compute discount at submission time using course properties
            price_details_submit = course.current_price_details
            disc_pct = price_details_submit['discount_percent'] if price_details_submit['has_offer'] else None
            final = price_details_submit['discounted_fee']
                
            if not existing_enrollment:
                enrollment = Enrollment(
                    student_id=current_user.student_id,
                    course_id=course_id,
                    payment_status='Submitted',
                    enrollment_status='Payment Submitted',
                    payment_reference=txn_ref,
                    discount_applied=disc_pct,
                    final_fee=final
                )
                db.session.add(enrollment)
                db.session.flush()
            else:
                enrollment = existing_enrollment
                enrollment.payment_status = 'Submitted'
                enrollment.enrollment_status = 'Payment Submitted'
                enrollment.payment_reference = txn_ref
                enrollment.discount_applied = disc_pct
                enrollment.final_fee = final
                
            filename = secure_filename(file.filename)
            unique_filename = f"pay_{enrollment.enrollment_id}_{int(datetime.utcnow().timestamp())}_{filename}"
            upload_dir = os.path.join(current_app.config['UPLOAD_FOLDER'], 'payments')
            os.makedirs(upload_dir, exist_ok=True)
            file.save(os.path.join(upload_dir, unique_filename))
            enrollment.payment_screenshot = f"uploads/payments/{unique_filename}"
            
            # Send Notification
            disc_msg = f" A {int(disc_pct)}% discount was applied!" if disc_pct else ""
            notif = Notification(
                student_id=current_user.student_id,
                title="Payment Submitted",
                message=f"Thank you. Your payment (Ref: {txn_ref}) for '{course.course_name}' (₹{final:.2f}) has been submitted and is pending verification.{disc_msg}"
            )
            db.session.add(notif)
            db.session.commit()
            
            flash('Your payment details have been submitted successfully! The administration will verify and approve your enrollment shortly.', 'success')
            return redirect(url_for('student.courses'))
            
    return render_template('student/contact_instructor.html',
                           course=course, form=form,
                           existing_enrollment=existing_enrollment,
                           active_offer=active_offer,
                           original_fee=original_fee,
                           discounted_fee=discounted_fee,
                           discount_amount=discount_amount)


@student_bp.route('/courses/<int:course_id>/submit-payment', methods=['POST'])
@login_required
@student_required
def submit_payment(course_id):
    enrollment = Enrollment.query.filter_by(
        student_id=current_user.student_id, course_id=course_id
    ).first_or_404()
    
    txn_ref = request.form.get('txn_reference', '').strip()
    if not txn_ref:
        flash('Please provide a payment reference (e.g. Transaction ID, receipt number).', 'danger')
        return redirect(url_for('student.courses'))
        
    enrollment.payment_status = 'Submitted'
    enrollment.enrollment_status = 'Payment Submitted'
    enrollment.payment_reference = txn_ref
    
    # Handle screenshot upload
    file = request.files.get('payment_screenshot')
    if file:
        filename = secure_filename(file.filename)
        unique_filename = f"pay_{enrollment.enrollment_id}_{int(datetime.utcnow().timestamp())}_{filename}"
        upload_dir = os.path.join(current_app.config['UPLOAD_FOLDER'], 'payments')
        os.makedirs(upload_dir, exist_ok=True)
        file.save(os.path.join(upload_dir, unique_filename))
        enrollment.payment_screenshot = f"uploads/payments/{unique_filename}"
    
    # Notify student
    notif = Notification(
        student_id=current_user.student_id,
        title="Payment Submitted",
        message=f"Thank you. Your payment details (Ref: {txn_ref}) for the course '{enrollment.course.course_name}' have been submitted and are pending verification."
    )
    db.session.add(notif)
    db.session.commit()
    
    flash('Payment details submitted successfully! The administration will verify your payment shortly.', 'success')
    return redirect(url_for('student.courses'))


@student_bp.route('/courses/<int:course_id>/view')
@login_required
@student_required
def view_course(course_id):
    # Verification that the course is approved
    enrollment = Enrollment.query.filter_by(
        student_id=current_user.student_id, course_id=course_id
    ).first()
    
    if not enrollment or enrollment.enrollment_status != 'Approved':
        flash('You must have an approved enrollment to view this course.', 'danger')
        return redirect(url_for('student.courses'))
        
    return render_template('student/view_course.html', course=enrollment.course)


@student_bp.route('/notifications')
@login_required
@student_required
def notifications():
    student_notifs = Notification.query.filter_by(
        student_id=current_user.student_id
    ).order_by(Notification.created_at.desc()).all()
    return render_template('student/notifications.html', notifications=student_notifs)


@student_bp.route('/notifications/read/<int:notification_id>')
@login_required
@student_required
def mark_read(notification_id):
    notif = Notification.query.filter_by(
        notification_id=notification_id, student_id=current_user.student_id
    ).first_or_404()
    notif.is_read = True
    db.session.commit()
    return redirect(url_for('student.notifications'))


@student_bp.route('/notifications/delete/<int:notification_id>', methods=['POST'])
@login_required
@student_required
def delete_notification(notification_id):
    notif = Notification.query.filter_by(
        notification_id=notification_id, student_id=current_user.student_id
    ).first_or_404()
    db.session.delete(notif)
    db.session.commit()
    flash('Notification deleted.', 'info')
    return redirect(url_for('student.notifications'))



@student_bp.route('/inquiries', methods=['GET', 'POST'])
@login_required
@student_required
def inquiries():
    # Load all active courses for the dropdown
    active_courses = Course.query.filter_by(status='Active').all()
    
    form = InquiryCreateForm()
    form.course_id.choices = [(c.course_id, c.course_name) for c in active_courses]
    
    # Pre-select course if passed in query string (from course page Inquiry button)
    pre_course_id = request.args.get('course_id', type=int)
    if pre_course_id and not form.is_submitted():
        form.course_id.data = pre_course_id
    
    if form.validate_on_submit():
        inquiry = Inquiry(
            student_id=current_user.student_id,
            course_id=form.course_id.data,
            subject=form.subject.data,
            message=form.message.data,
            status='Pending'
        )
        db.session.add(inquiry)
        db.session.commit()
        flash('Your inquiry has been submitted! The admin will reply shortly.', 'success')
        return redirect(url_for('student.inquiry_detail', inquiry_id=inquiry.inquiry_id))
    
    student_inquiries = Inquiry.query.filter_by(
        student_id=current_user.student_id
    ).order_by(Inquiry.created_at.desc()).all()
    
    return render_template('student/inquiries.html',
                           inquiries=student_inquiries,
                           form=form,
                           active_courses=active_courses,
                           pre_course_id=pre_course_id)


@student_bp.route('/inquiries/<int:inquiry_id>', methods=['GET', 'POST'])
@login_required
@student_required
def inquiry_detail(inquiry_id):
    inquiry = Inquiry.query.filter_by(
        inquiry_id=inquiry_id, student_id=current_user.student_id
    ).first_or_404()
    
    if request.method == 'POST':
        msg = request.form.get('reply_message', '').strip()
        if msg:
            reply = InquiryReply(
                inquiry_id=inquiry_id,
                sender_role='student',
                message=msg
            )
            # Reopen inquiry if it was closed
            if inquiry.status == 'Closed':
                inquiry.status = 'Pending'
            db.session.add(reply)
            db.session.commit()
            flash('Your reply has been sent.', 'success')
        return redirect(url_for('student.inquiry_detail', inquiry_id=inquiry_id))
    
    return render_template('student/inquiry_detail.html', inquiry=inquiry)

