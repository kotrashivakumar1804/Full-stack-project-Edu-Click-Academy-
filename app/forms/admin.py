from flask_wtf import FlaskForm
from flask_wtf.file import FileField, FileAllowed
from wtforms import StringField, TextAreaField, DecimalField, SelectField, PasswordField, DateField, SubmitField, SelectMultipleField
from wtforms.validators import DataRequired, Email, Length, Optional, Regexp, ValidationError
from app.models.student import Student

class CourseForm(FlaskForm):
    course_name = StringField('Course Name', validators=[
        DataRequired(message="Course Name is required."),
        Length(max=150)
    ])
    description = TextAreaField('Description', validators=[
        DataRequired(message="Course description is required.")
    ])
    duration = StringField('Duration', validators=[
        DataRequired(message="Course duration is required. (e.g. '8 Weeks', '3 Months')"),
        Length(max=50)
    ])
    fee = DecimalField('Course Fee (₹)', places=2, validators=[
        DataRequired(message="Course fee is required and must be numeric.")
    ])
    instructor_name = StringField('Instructor Name', validators=[
        DataRequired(message="Instructor name is required."),
        Length(max=100)
    ])
    instructor_email = StringField('Instructor Email', validators=[
        DataRequired(message="Instructor email is required."),
        Email(message="Invalid email address format."),
        Length(max=100)
    ])
    course_image = FileField('Course Cover Image', validators=[
        FileAllowed(['jpg', 'jpeg', 'png', 'webp'], 'Images only (jpg, jpeg, png, webp).')
    ])
    status = SelectField('Course Status', choices=[
        ('Active', 'Active'),
        ('Inactive', 'Inactive')
    ], default='Active', validators=[DataRequired()])
    submit = SubmitField('Submit Course')


class AnnouncementForm(FlaskForm):
    title = StringField('Announcement Title', validators=[
        DataRequired(message="Title is required."),
        Length(max=200)
    ])
    description = TextAreaField('Announcement Content', validators=[
        DataRequired(message="Content description is required.")
    ])
    is_offer = SelectField('Type', choices=[
        ('0', 'General Announcement'),
        ('1', 'Special Offer / Discount')
    ], default='0')
    discount_percent = DecimalField('Discount Percentage (%)', places=1, validators=[Optional()],
                                    description="e.g. 30 for 30% off. Leave blank for general announcements.")
    start_at = DateField('Offer Starts On (optional)', validators=[Optional()], format='%Y-%m-%d',
                         description="Leave blank to start immediately.")
    expires_at = DateField('Offer Expires On (optional)', validators=[Optional()], format='%Y-%m-%d',
                           description="Leave blank for no expiry.")
    courses = SelectMultipleField('Apply to Courses', coerce=int, validators=[Optional()],
                                  description="Select courses this offer applies to.")
    is_active = SelectField('Status', choices=[
        ('1', 'Active'),
        ('0', 'Inactive')
    ], default='1')
    submit = SubmitField('Publish Announcement')


class AdminStudentForm(FlaskForm):
    full_name = StringField('Full Name', validators=[
        DataRequired(message="Full Name is required."),
        Length(min=2, max=100)
    ])
    email = StringField('Email Address', validators=[
        DataRequired(message="Email address is required."),
        Email(message="Invalid email format."),
        Length(max=100)
    ])
    mobile = StringField('Mobile Number', validators=[
        DataRequired(message="Mobile number is required."),
        Regexp(r'^\+?[0-9\s\-()]{10,20}$', message="Invalid mobile number format.")
    ])
    gender = SelectField('Gender', choices=[
        ('Male', 'Male'),
        ('Female', 'Female'),
        ('Other', 'Other')
    ], validators=[DataRequired(message="Gender is required.")])
    password = PasswordField('Password', validators=[
        Optional(),
        Length(min=6, message="Password must be at least 6 characters long.")
    ])
    submit = SubmitField('Save Student')

    def __init__(self, student_id=None, *args, **kwargs):
        super(AdminStudentForm, self).__init__(*args, **kwargs)
        self.student_id = student_id

    def validate_email(self, email):
        query = Student.query.filter_by(email=email.data)
        if self.student_id:
            query = query.filter(Student.student_id != self.student_id)
        student = query.first()
        if student:
            raise ValidationError('Email address is already in use by another student.')
