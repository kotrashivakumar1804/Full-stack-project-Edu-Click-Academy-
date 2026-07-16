import os
from datetime import datetime, timedelta
from flask import Blueprint, render_template, redirect, url_for, flash, request, current_app, send_file, jsonify
from flask_login import login_required
from werkzeug.utils import secure_filename
from werkzeug.security import generate_password_hash
from app.extensions import db
from app.models.student import Student
from app.models.course import Course
from app.models.enrollment import Enrollment
from app.models.message import ContactMessage
from app.models.announcement import Announcement
from app.models.notification import Notification
from app.models.inquiry import Inquiry, InquiryReply
from app.forms.admin import CourseForm, AnnouncementForm, AdminStudentForm
from app.forms.contact import AdminReplyForm
from app.utils.decorators import admin_required
from app.utils.report_generator import generate_pdf_report, generate_excel_report

admin_bp = Blueprint('admin', __name__, url_prefix='/admin')

@admin_bp.route('/dashboard')
@login_required
@admin_required
def dashboard():
    total_students = Student.query.count()
    total_courses = Course.query.count()
    total_enrollments = Enrollment.query.count()
    total_messages = ContactMessage.query.count()
    
    # Recent Registrations
    recent_registrations = Student.query.order_by(Student.created_at.desc()).limit(5).all()
    
    return render_template('admin/dashboard.html',
                           total_students=total_students,
                           total_courses=total_courses,
                           total_enrollments=total_enrollments,
                           total_messages=total_messages,
                           recent_registrations=recent_registrations)


@admin_bp.route('/chart-data')
@login_required
@admin_required
def chart_data():
    """Returns registration stats and enrollment statistics in JSON for Chart.js."""
    # 1. Registrations over last 7 days
    today = datetime.utcnow().date()
    dates = [today - timedelta(days=i) for i in range(6, -1, -1)]
    date_labels = [d.strftime('%b %d') for d in dates]
    
    reg_counts = []
    for d in dates:
        start = datetime.combine(d, datetime.min.time())
        end = datetime.combine(d, datetime.max.time())
        count = Student.query.filter(Student.created_at.between(start, end)).count()
        reg_counts.append(count)
        
    # 2. Enrollment by course distribution
    courses = Course.query.all()
    course_labels = [c.course_name[:20] + '...' if len(c.course_name) > 20 else c.course_name for c in courses]
    enrollment_counts = [len(c.enrollments) for c in courses]
    
    return jsonify({
        'registrations': {
            'labels': date_labels,
            'data': reg_counts
        },
        'enrollments': {
            'labels': course_labels,
            'data': enrollment_counts
        }
    })


# --- STUDENT MANAGEMENT ---
@admin_bp.route('/students')
@login_required
@admin_required
def manage_students():
    search_query = request.args.get('q', '').strip()
    page = request.args.get('page', 1, type=int)
    
    query = Student.query
    if search_query:
        query = query.filter(
            (Student.full_name.like(f'%{search_query}%')) |
            (Student.email.like(f'%{search_query}%')) |
            (Student.mobile.like(f'%{search_query}%'))
        )
        
    paginated = query.order_by(Student.created_at.desc()).paginate(page=page, per_page=10, error_out=False)
    return render_template('admin/students.html', students=paginated.items, pagination=paginated, search_query=search_query)


@admin_bp.route('/students/add', methods=['GET', 'POST'])
@login_required
@admin_required
def add_student():
    form = AdminStudentForm()
    # For a new student, password is required
    if request.method == 'POST' and not form.password.data:
        form.password.errors.append("Password is required for registration.")
        
    if form.validate_on_submit() and form.password.data:
        hashed_password = generate_password_hash(form.password.data)
        student = Student(
            full_name=form.full_name.data,
            email=form.email.data.lower(),
            mobile=form.mobile.data,
            gender=form.gender.data,
            password=hashed_password
        )
        db.session.add(student)
        db.session.commit()
        
        # Notify student
        notif = Notification(
            student_id=student.student_id,
            title="Account Created",
            message="An account has been created for you by the administrator. Please update your profile information and change your password."
        )
        db.session.add(notif)
        db.session.commit()
        
        flash('Student added successfully!', 'success')
        return redirect(url_for('admin.manage_students'))
        
    return render_template('admin/student_form.html', form=form, title="Add Student")


@admin_bp.route('/students/edit/<int:student_id>', methods=['GET', 'POST'])
@login_required
@admin_required
def edit_student(student_id):
    student = Student.query.get_or_404(student_id)
    form = AdminStudentForm(student_id=student_id, obj=student)
    
    if form.validate_on_submit():
        student.full_name = form.full_name.data
        student.email = form.email.data.lower()
        student.mobile = form.mobile.data
        student.gender = form.gender.data
        
        if form.password.data:
            student.password = generate_password_hash(form.password.data)
            
            # Send Notification
            notif = Notification(
                student_id=student.student_id,
                title="Credentials Updated",
                message="Your account password was updated by the administrator."
            )
            db.session.add(notif)
            
        db.session.commit()
        flash('Student profile details updated successfully.', 'success')
        return redirect(url_for('admin.manage_students'))
        
    return render_template('admin/student_form.html', form=form, title="Edit Student", student=student)


@admin_bp.route('/students/delete/<int:student_id>', methods=['POST'])
@login_required
@admin_required
def delete_student(student_id):
    student = Student.query.get_or_404(student_id)
    db.session.delete(student)
    db.session.commit()
    flash('Student account deleted.', 'info')
    return redirect(url_for('admin.manage_students'))


# --- COURSE MANAGEMENT ---
@admin_bp.route('/courses')
@login_required
@admin_required
def manage_courses():
    search_query = request.args.get('q', '').strip()
    page = request.args.get('page', 1, type=int)
    
    query = Course.query
    if search_query:
        query = query.filter(
            (Course.course_name.like(f'%{search_query}%')) |
            (Course.instructor_name.like(f'%{search_query}%'))
        )
        
    paginated = query.paginate(page=page, per_page=10, error_out=False)
    return render_template('admin/courses.html', courses=paginated.items, pagination=paginated, search_query=search_query)


@admin_bp.route('/courses/add', methods=['GET', 'POST'])
@login_required
@admin_required
def add_course():
    form = CourseForm()
    if form.validate_on_submit():
        course = Course(
            course_name=form.course_name.data,
            description=form.description.data,
            duration=form.duration.data,
            fee=form.fee.data,
            instructor_name=form.instructor_name.data,
            instructor_email=form.instructor_email.data,
            status=form.status.data
        )
        
        file = form.course_image.data
        if file:
            filename = secure_filename(file.filename)
            unique_filename = f"course_{int(datetime.utcnow().timestamp())}_{filename}"
            upload_dir = os.path.join(current_app.config['UPLOAD_FOLDER'], 'courses')
            os.makedirs(upload_dir, exist_ok=True)
            file.save(os.path.join(upload_dir, unique_filename))
            course.course_image = f"uploads/courses/{unique_filename}"
            
        db.session.add(course)
        db.session.commit()
        
        # Notify all students of new course
        students = Student.query.all()
        for s in students:
            notif = Notification(
                student_id=s.student_id,
                title="New Course Added",
                message=f"A new course '{course.course_name}' has been added. Explore it in the course directory!"
            )
            db.session.add(notif)
        db.session.commit()
        
        flash('Course published successfully!', 'success')
        return redirect(url_for('admin.manage_courses'))
        
    return render_template('admin/course_form.html', form=form, title="Add Course")


@admin_bp.route('/courses/edit/<int:course_id>', methods=['GET', 'POST'])
@login_required
@admin_required
def edit_course(course_id):
    course = Course.query.get_or_404(course_id)
    form = CourseForm(obj=course)
    
    if form.validate_on_submit():
        course.course_name = form.course_name.data
        course.description = form.description.data
        course.duration = form.duration.data
        course.fee = form.fee.data
        course.instructor_name = form.instructor_name.data
        course.instructor_email = form.instructor_email.data
        course.status = form.status.data
        
        file = form.course_image.data
        if file:
            filename = secure_filename(file.filename)
            unique_filename = f"course_{course.course_id}_{int(datetime.utcnow().timestamp())}_{filename}"
            upload_dir = os.path.join(current_app.config['UPLOAD_FOLDER'], 'courses')
            os.makedirs(upload_dir, exist_ok=True)
            file.save(os.path.join(upload_dir, unique_filename))
            course.course_image = f"uploads/courses/{unique_filename}"
            
        db.session.commit()
        flash('Course settings updated successfully.', 'success')
        return redirect(url_for('admin.manage_courses'))
        
    return render_template('admin/course_form.html', form=form, title="Edit Course", course=course)


@admin_bp.route('/courses/toggle-status/<int:course_id>', methods=['POST'])
@login_required
@admin_required
def toggle_course_status(course_id):
    course = Course.query.get_or_404(course_id)
    course.status = 'Inactive' if course.status == 'Active' else 'Active'
    db.session.commit()
    flash(f"Course '{course.course_name}' status changed to {course.status}.", 'success')
    return redirect(url_for('admin.manage_courses'))


@admin_bp.route('/courses/delete/<int:course_id>', methods=['POST'])
@login_required
@admin_required
def delete_course(course_id):
    course = Course.query.get_or_404(course_id)
    db.session.delete(course)
    db.session.commit()
    flash('Course has been deleted from catalog.', 'info')
    return redirect(url_for('admin.manage_courses'))


# --- ENROLLMENT MANAGEMENT ---
@admin_bp.route('/enrollments')
@login_required
@admin_required
def manage_enrollments():
    page = request.args.get('page', 1, type=int)
    paginated = Enrollment.query.order_by(Enrollment.enrollment_date.desc()).paginate(page=page, per_page=10, error_out=False)
    return render_template('admin/enrollments.html', enrollments=paginated.items, pagination=paginated)


@admin_bp.route('/enrollments/approve/<int:enrollment_id>', methods=['POST'])
@login_required
@admin_required
def approve_enrollment(enrollment_id):
    enrollment = Enrollment.query.get_or_404(enrollment_id)
    enrollment.enrollment_status = 'Approved'
    enrollment.payment_status = 'Paid'
    
    # Notify student
    notif = Notification(
        student_id=enrollment.student_id,
        title="Enrollment Approved!",
        message=f"Congratulations! Your enrollment request for '{enrollment.course.course_name}' has been approved. You can now access full course material."
    )
    db.session.add(notif)
    db.session.commit()
    
    flash(f"Enrollment approved for {enrollment.student.full_name}.", 'success')
    return redirect(url_for('admin.manage_enrollments'))


@admin_bp.route('/enrollments/reject/<int:enrollment_id>', methods=['POST'])
@login_required
@admin_required
def reject_enrollment(enrollment_id):
    enrollment = Enrollment.query.get_or_404(enrollment_id)
    enrollment.enrollment_status = 'Rejected'
    enrollment.payment_status = 'Unpaid'
    
    # Notify student
    notif = Notification(
        student_id=enrollment.student_id,
        title="Enrollment Inquiry Update",
        message=f"Your enrollment request for '{enrollment.course.course_name}' has been rejected. Please review payment or contact admin."
    )
    db.session.add(notif)
    db.session.commit()
    
    flash(f"Enrollment request rejected for {enrollment.student.full_name}.", 'warning')
    return redirect(url_for('admin.manage_enrollments'))


@admin_bp.route('/enrollments/update-payment/<int:enrollment_id>', methods=['POST'])
@login_required
@admin_required
def update_payment_status(enrollment_id):
    enrollment = Enrollment.query.get_or_404(enrollment_id)
    status = request.form.get('payment_status')
    if status in ['Unpaid', 'Submitted', 'Paid']:
        enrollment.payment_status = status
        db.session.commit()
        flash('Payment status updated.', 'success')
    return redirect(url_for('admin.manage_enrollments'))


# --- CONTACT MESSAGES ---
@admin_bp.route('/messages')
@login_required
@admin_required
def manage_messages():
    search_query = request.args.get('q', '').strip()
    page = request.args.get('page', 1, type=int)
    
    query = ContactMessage.query
    if search_query:
        query = query.filter(
            (ContactMessage.name.like(f'%{search_query}%')) |
            (ContactMessage.email.like(f'%{search_query}%')) |
            (ContactMessage.subject.like(f'%{search_query}%'))
        )
        
    paginated = query.order_by(ContactMessage.created_at.desc()).paginate(page=page, per_page=10, error_out=False)
    form = AdminReplyForm()
    return render_template('admin/messages.html', messages=paginated.items, pagination=paginated, search_query=search_query, form=form)


@admin_bp.route('/messages/reply/<int:message_id>', methods=['POST'])
@login_required
@admin_required
def reply_message(message_id):
    msg = ContactMessage.query.get_or_404(message_id)
    form = AdminReplyForm()
    if form.validate_on_submit():
        msg.admin_reply = form.reply_message.data
        db.session.commit()
        
        # Log simulated reply send
        print(f"[MOCK EMAIL] Reply sent to {msg.name} ({msg.email}) for message subject '{msg.subject}': {msg.admin_reply}")
        flash('Reply registered and logged successfully.', 'success')
    return redirect(url_for('admin.manage_messages'))


@admin_bp.route('/messages/delete/<int:message_id>', methods=['POST'])
@login_required
@admin_required
def delete_message(message_id):
    msg = ContactMessage.query.get_or_404(message_id)
    db.session.delete(msg)
    db.session.commit()
    flash('Message deleted.', 'info')
    return redirect(url_for('admin.manage_messages'))


# --- INQUIRY MANAGEMENT ---
@admin_bp.route('/inquiries')
@login_required
@admin_required
def manage_inquiries():
    course_filter = request.args.get('course_id', type=int)
    status_filter = request.args.get('status', '').strip()
    page = request.args.get('page', 1, type=int)
    
    query = Inquiry.query
    if course_filter:
        query = query.filter_by(course_id=course_filter)
    if status_filter and status_filter in ['Pending', 'Replied', 'Closed']:
        query = query.filter_by(status=status_filter)
    
    paginated = query.order_by(Inquiry.created_at.desc()).paginate(page=page, per_page=15, error_out=False)
    courses = Course.query.order_by(Course.course_name).all()
    
    return render_template('admin/inquiries.html',
                           inquiries=paginated.items,
                           pagination=paginated,
                           courses=courses,
                           course_filter=course_filter,
                           status_filter=status_filter)


@admin_bp.route('/inquiries/<int:inquiry_id>', methods=['GET', 'POST'])
@login_required
@admin_required
def inquiry_detail(inquiry_id):
    inquiry = Inquiry.query.get_or_404(inquiry_id)
    
    if request.method == 'POST':
        action = request.form.get('action')
        
        if action == 'reply':
            msg = request.form.get('reply_message', '').strip()
            if msg:
                reply = InquiryReply(
                    inquiry_id=inquiry_id,
                    sender_role='admin',
                    message=msg
                )
                inquiry.status = 'Replied'
                db.session.add(reply)
                
                # Notify the student if registered, otherwise print mock email
                if inquiry.student_id:
                    notif = Notification(
                        student_id=inquiry.student_id,
                        title=f"New Reply on Your Inquiry: {inquiry.subject}",
                        message=f"The admin has replied to your inquiry about '{inquiry.course.course_name if inquiry.course else 'General Inquiry'}'. Check your Inquiry inbox."
                    )
                    db.session.add(notif)
                    db.session.commit()
                    flash('Reply sent to student successfully.', 'success')
                else:
                    db.session.commit()
                    print(f"[MOCK EMAIL] Reply sent to guest {inquiry.name} ({inquiry.email}) for inquiry subject '{inquiry.subject}': {msg}")
                    flash('Reply registered and logged successfully.', 'success')
            else:
                flash('Reply message cannot be empty.', 'danger')
                
        elif action == 'status':
            new_status = request.form.get('status')
            if new_status in ['Pending', 'Replied', 'Closed']:
                inquiry.status = new_status
                db.session.commit()
                flash(f'Inquiry status updated to "{new_status}".', 'success')
        
        return redirect(url_for('admin.inquiry_detail', inquiry_id=inquiry_id))
    
    return render_template('admin/inquiry_detail.html', inquiry=inquiry)


@admin_bp.route('/inquiries/<int:inquiry_id>/delete', methods=['POST'])
@login_required
@admin_required
def delete_inquiry(inquiry_id):
    inquiry = Inquiry.query.get_or_404(inquiry_id)
    db.session.delete(inquiry)
    db.session.commit()
    flash('Inquiry deleted successfully.', 'info')
    return redirect(url_for('admin.manage_inquiries'))


# --- ANNOUNCEMENTS ---
@admin_bp.route('/announcements')
@login_required
@admin_required
def manage_announcements():
    page = request.args.get('page', 1, type=int)
    paginated = Announcement.query.order_by(Announcement.created_at.desc()).paginate(page=page, per_page=10, error_out=False)
    return render_template('admin/announcements.html', announcements=paginated.items, pagination=paginated)


@admin_bp.route('/announcements/add', methods=['GET', 'POST'])
@login_required
@admin_required
def add_announcement():
    active_courses = Course.query.filter_by(status='Active').order_by(Course.course_name).all()
    form = AnnouncementForm()
    form.courses.choices = [(c.course_id, c.course_name) for c in active_courses]
    
    if form.validate_on_submit():
        ann = Announcement(
            title=form.title.data,
            description=form.description.data,
            is_offer=bool(int(form.is_offer.data)),
            discount_percent=float(form.discount_percent.data) if form.discount_percent.data else None,
            is_active=bool(int(form.is_active.data)),
            start_at=datetime.combine(form.start_at.data, datetime.min.time()) if form.start_at.data else None,
            expires_at=datetime.combine(form.expires_at.data, datetime.max.time()) if form.expires_at.data else None,
        )
        if form.courses.data:
            ann.courses = [db.session.get(Course, cid) for cid in form.courses.data if db.session.get(Course, cid)]
            
        db.session.add(ann)
        
        # Send Notification to all students for announcements
        students = Student.query.all()
        for s in students:
            msg = f"Administrator posted: '{ann.title}'."
            if ann.is_offer and ann.discount_percent:
                msg = f"🎉 Special Offer! {int(ann.discount_percent)}% OFF on courses — {ann.title}. Enroll now to grab the deal!"
            notif = Notification(
                student_id=s.student_id,
                title=f"{'🎉 Offer: ' if ann.is_offer else 'Announcement: '}{ann.title}",
                message=msg
            )
            db.session.add(notif)
            
        db.session.commit()
        flash('Announcement published and notifications sent.', 'success')
        return redirect(url_for('admin.manage_announcements'))
        
    return render_template('admin/announcement_form.html', form=form, title="Post Announcement")


@admin_bp.route('/announcements/edit/<int:announcement_id>', methods=['GET', 'POST'])
@login_required
@admin_required
def edit_announcement(announcement_id):
    ann = Announcement.query.get_or_404(announcement_id)
    active_courses = Course.query.filter_by(status='Active').order_by(Course.course_name).all()
    form = AnnouncementForm(obj=ann)
    form.courses.choices = [(c.course_id, c.course_name) for c in active_courses]
    
    if request.method == 'GET':
        form.courses.data = [c.course_id for c in ann.courses]
        
    if form.validate_on_submit():
        ann.title = form.title.data
        ann.description = form.description.data
        ann.is_offer = bool(int(form.is_offer.data))
        ann.discount_percent = float(form.discount_percent.data) if form.discount_percent.data else None
        ann.is_active = bool(int(form.is_active.data))
        ann.start_at = datetime.combine(form.start_at.data, datetime.min.time()) if form.start_at.data else None
        ann.expires_at = datetime.combine(form.expires_at.data, datetime.max.time()) if form.expires_at.data else None
        
        if form.courses.data:
            ann.courses = [db.session.get(Course, cid) for cid in form.courses.data if db.session.get(Course, cid)]
        else:
            ann.courses = []
            
        db.session.commit()
        flash('Announcement updated successfully.', 'success')
        return redirect(url_for('admin.manage_announcements'))
    return render_template('admin/announcement_form.html', form=form, title="Edit Announcement", announcement=ann)


@admin_bp.route('/announcements/delete/<int:announcement_id>', methods=['POST'])
@login_required
@admin_required
def delete_announcement(announcement_id):
    ann = Announcement.query.get_or_404(announcement_id)
    db.session.delete(ann)
    db.session.commit()
    flash('Announcement deleted.', 'info')
    return redirect(url_for('admin.manage_announcements'))


# --- REPORTS GENERATION ---
@admin_bp.route('/reports')
@login_required
@admin_required
def reports():
    return render_template('admin/reports.html')


@admin_bp.route('/reports/export')
@login_required
@admin_required
def export_report():
    report_type = request.args.get('type')
    fmt = request.args.get('format', 'pdf').lower()
    
    if report_type == 'student':
        title = "Student Registry Report"
        headers = ["ID", "Full Name", "Email", "Mobile", "Gender", "Registered At"]
        students = Student.query.order_by(Student.student_id).all()
        data = [[s.student_id, s.full_name, s.email, s.mobile, s.gender, s.created_at] for s in students]
        landscape_mode = False
        
    elif report_type == 'course':
        title = "Course Syllabus Report"
        headers = ["ID", "Course Name", "Duration", "Fee (₹)", "Instructor", "Instructor Email", "Status", "Enrollments"]
        courses = Course.query.order_by(Course.course_id).all()
        data = [[c.course_id, c.course_name, c.duration, f"{c.fee:.2f}", c.instructor_name, c.instructor_email, c.status, len(c.enrollments)] for c in courses]
        landscape_mode = True
        
    elif report_type == 'enrollment':
        title = "Enrollment & Revenue Report"
        headers = ["ID", "Student ID", "Student Name", "Course ID", "Course Name", "Payment Status", "Enrollment Status", "Date"]
        enrollments = Enrollment.query.order_by(Enrollment.enrollment_id).all()
        data = [[e.enrollment_id, e.student_id, e.student.full_name, e.course_id, e.course.course_name, e.payment_status, e.enrollment_status, e.enrollment_date] for e in enrollments]
        landscape_mode = True
        
    elif report_type == 'contact':
        title = "Contact Messages Report"
        headers = ["ID", "Name", "Email", "Subject", "Message Snippet", "Replied", "Date"]
        messages = ContactMessage.query.order_by(ContactMessage.message_id).all()
        data = [
            [
                m.message_id, 
                m.name, 
                m.email, 
                m.subject, 
                m.message[:30] + '...' if len(m.message) > 30 else m.message, 
                "Yes" if m.admin_reply else "No", 
                m.created_at
            ] for m in messages
        ]
        landscape_mode = True
    else:
        flash('Invalid report type specified.', 'danger')
        return redirect(url_for('admin.reports'))
        
    # Generate and deliver based on format
    if fmt == 'pdf':
        buffer = generate_pdf_report(title, headers, data, landscape_mode=landscape_mode)
        filename = f"{report_type}_report_{datetime.now().strftime('%Y%m%d')}.pdf"
        mimetype = "application/pdf"
    elif fmt == 'excel':
        buffer = generate_excel_report(report_type.capitalize(), headers, data)
        filename = f"{report_type}_report_{datetime.now().strftime('%Y%m%d')}.xlsx"
        mimetype = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    else:
        flash('Invalid report format specified.', 'danger')
        return redirect(url_for('admin.reports'))
        
    return send_file(
        buffer,
        as_attachment=True,
        download_name=filename,
        mimetype=mimetype
    )


# --- OFFERS MANAGEMENT ---
@admin_bp.route('/offers')
@login_required
@admin_required
def manage_offers():
    page = request.args.get('page', 1, type=int)
    paginated = Announcement.query.filter_by(is_offer=True).order_by(Announcement.created_at.desc()).paginate(page=page, per_page=10, error_out=False)
    return render_template('admin/offers.html', offers=paginated.items, pagination=paginated)

@admin_bp.route('/offers/add', methods=['GET', 'POST'])
@login_required
@admin_required
def add_offer():
    active_courses = Course.query.filter_by(status='Active').order_by(Course.course_name).all()
    form = AnnouncementForm()
    form.courses.choices = [(c.course_id, c.course_name) for c in active_courses]
    if request.method == 'GET':
        form.is_offer.data = '1'
        
    if form.validate_on_submit():
        ann = Announcement(
            title=form.title.data,
            description=form.description.data,
            is_offer=True,
            discount_percent=float(form.discount_percent.data) if form.discount_percent.data else None,
            is_active=bool(int(form.is_active.data)),
            start_at=datetime.combine(form.start_at.data, datetime.min.time()) if form.start_at.data else None,
            expires_at=datetime.combine(form.expires_at.data, datetime.max.time()) if form.expires_at.data else None,
        )
        if form.courses.data:
            ann.courses = [db.session.get(Course, cid) for cid in form.courses.data if db.session.get(Course, cid)]
            
        db.session.add(ann)
        
        # Send Notification to all students for offers
        from app.models.student import Student
        students = Student.query.all()
        for s in students:
            msg = f"🎉 Special Offer! {int(ann.discount_percent)}% OFF on courses — {ann.title}. Enroll now to grab the deal!"
            notif = Notification(
                student_id=s.student_id,
                title=f"🎉 Offer: {ann.title}",
                message=msg
            )
            db.session.add(notif)
            
        db.session.commit()
        flash('Special Offer published successfully.', 'success')
        return redirect(url_for('admin.manage_offers'))
        
    return render_template('admin/announcement_form.html', form=form, title="Post Special Offer", is_offer_mode=True)

@admin_bp.route('/offers/edit/<int:announcement_id>', methods=['GET', 'POST'])
@login_required
@admin_required
def edit_offer(announcement_id):
    ann = Announcement.query.get_or_404(announcement_id)
    active_courses = Course.query.filter_by(status='Active').order_by(Course.course_name).all()
    form = AnnouncementForm(obj=ann)
    form.courses.choices = [(c.course_id, c.course_name) for c in active_courses]
    
    if request.method == 'GET':
        form.courses.data = [c.course_id for c in ann.courses]
        form.is_offer.data = '1'
        
    if form.validate_on_submit():
        ann.title = form.title.data
        ann.description = form.description.data
        ann.is_offer = True
        ann.discount_percent = float(form.discount_percent.data) if form.discount_percent.data else None
        ann.is_active = bool(int(form.is_active.data))
        ann.start_at = datetime.combine(form.start_at.data, datetime.min.time()) if form.start_at.data else None
        ann.expires_at = datetime.combine(form.expires_at.data, datetime.max.time()) if form.expires_at.data else None
        
        if form.courses.data:
            ann.courses = [db.session.get(Course, cid) for cid in form.courses.data if db.session.get(Course, cid)]
        else:
            ann.courses = []
            
        db.session.commit()
        flash('Special Offer updated successfully.', 'success')
        return redirect(url_for('admin.manage_offers'))
    return render_template('admin/announcement_form.html', form=form, title="Edit Special Offer", announcement=ann, is_offer_mode=True)

@admin_bp.route('/offers/delete/<int:announcement_id>', methods=['POST'])
@login_required
@admin_required
def delete_offer(announcement_id):
    ann = Announcement.query.get_or_404(announcement_id)
    db.session.delete(ann)
    db.session.commit()
    flash('Special Offer deleted.', 'info')
    return redirect(url_for('admin.manage_offers'))


# --- STUDENT ACTIVITY TRACKING ---
@admin_bp.route('/student-activity', methods=['GET'])
@login_required
@admin_required
def student_activity():
    from datetime import timedelta
    now = datetime.utcnow()
    
    # 1. Quick Statistics
    total_students = Student.query.count()
    
    # Active Today (last_login >= today 00:00:00)
    today_start = datetime.combine(now.date(), datetime.min.time())
    active_today = Student.query.filter(Student.last_login >= today_start).count()
    
    # Active in Last 15 Days
    active_15_days_ago = now - timedelta(days=15)
    active_15_days = Student.query.filter(Student.last_login >= active_15_days_ago).count()
    
    # Inactive for More Than 15 Days: last_login < 15 days ago OR (last_login is None and created_at < 15 days ago)
    inactive_15_days = Student.query.filter(
        (Student.last_login < active_15_days_ago) | 
        ((Student.last_login == None) & (Student.created_at < active_15_days_ago))
    ).count()
    
    # Never Logged In
    never_logged_in = Student.query.filter(Student.last_login == None).count()
    
    stats = {
        'total_students': total_students,
        'active_today': active_today,
        'active_15_days': active_15_days,
        'inactive_15_days': inactive_15_days,
        'never_logged_in': never_logged_in
    }
    
    # 2. Filters & Search & Sorting query logic
    filter_val = request.args.get('filter', '').strip()
    search_val = request.args.get('search', '').strip()
    sort_val = request.args.get('sort', 'newest').strip()
    
    query = Student.query
    
    # Search filter
    if search_val:
        query = query.filter(
            (Student.full_name.like(f"%{search_val}%")) |
            (Student.email.like(f"%{search_val}%")) |
            (Student.student_id.like(f"%{search_val}%"))
        )
        
    # Activity filters
    if filter_val == 'active_today':
        query = query.filter(Student.last_login >= today_start)
    elif filter_val == 'active_7':
        query = query.filter(Student.last_login >= now - timedelta(days=7))
    elif filter_val == 'active_15':
        query = query.filter(Student.last_login >= now - timedelta(days=15))
    elif filter_val == 'active_30':
        query = query.filter(Student.last_login >= now - timedelta(days=30))
    elif filter_val == 'inactive_7':
        query = query.filter(
            (Student.last_login < now - timedelta(days=7)) |
            ((Student.last_login == None) & (Student.created_at < now - timedelta(days=7)))
        )
    elif filter_val == 'inactive_15':
        query = query.filter(
            (Student.last_login < now - timedelta(days=15)) |
            ((Student.last_login == None) & (Student.created_at < now - timedelta(days=15)))
        )
    elif filter_val == 'inactive_30':
        query = query.filter(
            (Student.last_login < now - timedelta(days=30)) |
            ((Student.last_login == None) & (Student.created_at < now - timedelta(days=30)))
        )
    elif filter_val == 'inactive_60':
        query = query.filter(
            (Student.last_login < now - timedelta(days=60)) |
            ((Student.last_login == None) & (Student.created_at < now - timedelta(days=60)))
        )
        
    # Sorting
    if sort_val == 'newest':
        query = query.order_by(Student.last_login.desc().nullslast())
    elif sort_val == 'oldest':
        query = query.order_by(Student.last_login.asc().nullsfirst())
    elif sort_val == 'most_active':
        query = query.order_by(Student.login_count.desc())
    elif sort_val == 'least_active':
        query = query.order_by(Student.login_count.asc())
        
    # Pagination
    page = request.args.get('page', 1, type=int)
    paginated = query.paginate(page=page, per_page=10, error_out=False)
    
    # Calculate extra fields for display
    students_list = []
    for s in paginated.items:
        days_since = None
        if s.last_login:
            days_since = (now - s.last_login).days
        else:
            days_since = (now - s.created_at).days
            
        # Determine status: Active if logged in within 30 days, else Inactive
        status = "Active"
        if s.last_login:
            if (now - s.last_login).days > 30:
                status = "Inactive"
        else:
            status = "Inactive"
            
        students_list.append({
            'student_id': s.student_id,
            'full_name': s.full_name,
            'email': s.email,
            'mobile': s.mobile,
            'last_login': s.last_login,
            'login_count': s.login_count,
            'status': status,
            'days_since': days_since
        })
        
    return render_template('admin/student_activity.html',
                           students=students_list,
                           pagination=paginated,
                           stats=stats,
                           filter_val=filter_val,
                           search_val=search_val,
                           sort_val=sort_val)

@admin_bp.route('/student-activity/export', methods=['GET'])
@login_required
@admin_required
def export_student_activity():
    from datetime import timedelta
    fmt = request.args.get('format', 'excel').strip()
    filter_val = request.args.get('filter', '').strip()
    search_val = request.args.get('search', '').strip()
    sort_val = request.args.get('sort', 'newest').strip()
    
    now = datetime.utcnow()
    today_start = datetime.combine(now.date(), datetime.min.time())
    
    query = Student.query
    
    # Apply filters, search, sorting
    if search_val:
        query = query.filter(
            (Student.full_name.like(f"%{search_val}%")) |
            (Student.email.like(f"%{search_val}%")) |
            (Student.student_id.like(f"%{search_val}%"))
        )
        
    if filter_val == 'active_today':
        query = query.filter(Student.last_login >= today_start)
    elif filter_val == 'active_7':
        query = query.filter(Student.last_login >= now - timedelta(days=7))
    elif filter_val == 'active_15':
        query = query.filter(Student.last_login >= now - timedelta(days=15))
    elif filter_val == 'active_30':
        query = query.filter(Student.last_login >= now - timedelta(days=30))
    elif filter_val == 'inactive_7':
        query = query.filter(
            (Student.last_login < now - timedelta(days=7)) |
            ((Student.last_login == None) & (Student.created_at < now - timedelta(days=7)))
        )
    elif filter_val == 'inactive_15':
        query = query.filter(
            (Student.last_login < now - timedelta(days=15)) |
            ((Student.last_login == None) & (Student.created_at < now - timedelta(days=15)))
        )
    elif filter_val == 'inactive_30':
        query = query.filter(
            (Student.last_login < now - timedelta(days=30)) |
            ((Student.last_login == None) & (Student.created_at < now - timedelta(days=30)))
        )
    elif filter_val == 'inactive_60':
        query = query.filter(
            (Student.last_login < now - timedelta(days=60)) |
            ((Student.last_login == None) & (Student.created_at < now - timedelta(days=60)))
        )
        
    if sort_val == 'newest':
        query = query.order_by(Student.last_login.desc().nullslast())
    elif sort_val == 'oldest':
        query = query.order_by(Student.last_login.asc().nullsfirst())
    elif sort_val == 'most_active':
        query = query.order_by(Student.login_count.desc())
    elif sort_val == 'least_active':
        query = query.order_by(Student.login_count.asc())
        
    students = query.all()
    
    headers = [
        "Student ID", "Full Name", "Email Address", "Mobile Number",
        "Last Login", "Total Logins", "Account Status", "Days Since Last Login"
    ]
    
    data = []
    for s in students:
        days_since = "Never"
        if s.last_login:
            days_since = str((now - s.last_login).days)
            
        status = "Active"
        if s.last_login:
            if (now - s.last_login).days > 30:
                status = "Inactive"
        else:
            status = "Inactive"
            
        last_login_str = s.last_login.strftime('%Y-%m-%d %H:%M') if s.last_login else "Never"
        
        data.append([
            s.student_id,
            s.full_name,
            s.email,
            s.mobile,
            last_login_str,
            s.login_count,
            status,
            days_since
        ])
        
    title = f"Student Login Activity Report"
    
    if fmt == 'pdf':
        buffer = generate_pdf_report(title, headers, data, landscape_mode=True)
        filename = f"student_activity_{now.strftime('%Y%m%d')}.pdf"
        mimetype = "application/pdf"
    else:
        buffer = generate_excel_report("Activity", headers, data)
        filename = f"student_activity_{now.strftime('%Y%m%d')}.xlsx"
        mimetype = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        
    return send_file(
        buffer,
        as_attachment=True,
        download_name=filename,
        mimetype=mimetype
    )
