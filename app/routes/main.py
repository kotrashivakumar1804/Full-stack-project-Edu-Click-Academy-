from flask import Blueprint, render_template, request, flash, redirect, url_for
from datetime import datetime
from app.extensions import db
from app.models.course import Course
from app.models.message import ContactMessage
from app.models.announcement import Announcement
from app.forms.contact import ContactForm

main_bp = Blueprint('main', __name__)

def get_active_offer():
    """Returns the highest active discount announcement, or None."""
    offers = Announcement.query.filter_by(is_offer=True, is_active=True).all()
    valid_offers = [o for o in offers if o.is_valid_offer]
    if not valid_offers:
        return None
    return max(valid_offers, key=lambda x: x.discount_percent)

@main_bp.route('/')
def home():
    # Fetch 3 active courses as featured courses
    featured_courses = Course.query.filter_by(status='Active').limit(3).all()
    # Fetch latest announcements/offers
    latest_announcements = Announcement.query.order_by(Announcement.created_at.desc()).limit(3).all()
    active_offer = get_active_offer()
    return render_template('main/home.html', featured_courses=featured_courses,
                           announcements=latest_announcements, active_offer=active_offer)

@main_bp.route('/about')
def about():
    return render_template('main/about.html')

@main_bp.route('/courses')
def courses():
    search_query = request.args.get('q', '').strip()
    
    # Base query: only active courses are visible to the public
    query = Course.query.filter_by(status='Active')
    
    if search_query:
        query = query.filter(
            (Course.course_name.like(f'%{search_query}%')) |
            (Course.instructor_name.like(f'%{search_query}%')) |
            (Course.description.like(f'%{search_query}%'))
        )
        
    # Pagination: 6 courses per page
    page = request.args.get('page', 1, type=int)
    paginated_courses = query.paginate(page=page, per_page=6, error_out=False)
    
    active_offer = get_active_offer()
    return render_template('main/courses.html', 
                           courses=paginated_courses.items, 
                           pagination=paginated_courses,
                           search_query=search_query,
                           active_offer=active_offer)

@main_bp.route('/courses/<int:course_id>')
def course_details(course_id):
    course = Course.query.get_or_404(course_id)
    if course.status != 'Active':
        flash('This course is currently not available.', 'warning')
        return redirect(url_for('main.courses'))
    return render_template('main/course_details.html', course=course)

@main_bp.route('/contact', methods=['GET', 'POST'])
def contact():
    form = ContactForm()
    if form.validate_on_submit():
        msg = ContactMessage(
            name=form.name.data,
            email=form.email.data,
            subject=form.subject.data,
            message=form.message.data
        )
        db.session.add(msg)
        db.session.commit()
        flash('Your message has been sent successfully! Our team will get back to you shortly.', 'success')
        return redirect(url_for('main.contact'))
        
    return render_template('main/contact.html', form=form)


@main_bp.route('/inquiry', methods=['GET', 'POST'])
def public_inquiry():
    from app.forms.contact import PublicInquiryForm
    from app.models.inquiry import Inquiry
    
    active_courses = Course.query.filter_by(status='Active').order_by(Course.course_name).all()
    form = PublicInquiryForm()
    form.course_id.choices = [(-1, 'General Inquiry (No specific course)')] + [(c.course_id, c.course_name) for c in active_courses]
    
    if form.validate_on_submit():
        selected_course_id = form.course_id.data
        course_id = None if selected_course_id <= 0 else selected_course_id
        
        inquiry = Inquiry(
            name=form.name.data,
            email=form.email.data,
            mobile=form.mobile.data,
            course_id=course_id,
            subject=form.subject.data,
            message=form.message.data,
            status='Pending'
        )
        db.session.add(inquiry)
        db.session.commit()
        flash('Your inquiry has been submitted successfully! Our team will get back to you shortly.', 'success')
        return redirect(url_for('main.public_inquiry'))
        
    return render_template('main/inquiry.html', form=form)
