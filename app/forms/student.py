from flask_wtf import FlaskForm
from flask_wtf.file import FileField, FileAllowed
from wtforms import StringField, DateField, SelectField, PasswordField, SubmitField
from wtforms.validators import DataRequired, Email, Length, EqualTo, ValidationError, Regexp
from flask_login import current_user
from app.models.student import Student

class EditProfileForm(FlaskForm):
    full_name = StringField('Full Name', validators=[
        DataRequired(message="Full Name is required."),
        Length(min=2, max=100, message="Name must be between 2 and 100 characters.")
    ])
    email = StringField('Email Address', validators=[
        DataRequired(message="Email address is required."),
        Email(message="Invalid email address format."),
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
    ], validators=[DataRequired(message="Please select a gender.")])
    profile_picture = FileField('Profile Picture', validators=[
        FileAllowed(['jpg', 'jpeg', 'png', 'webp'], 'Images only (jpg, jpeg, png, webp).')
    ])
    submit = SubmitField('Save Changes')

    def validate_email(self, email):
        if email.data != current_user.email:
            student = Student.query.filter_by(email=email.data).first()
            if student:
                raise ValidationError('Email address is already in use by another student.')
                
            from app.models.admin import Admin
            admin = Admin.query.filter_by(email=email.data).first()
            if admin:
                raise ValidationError('Email address is already in use.')


class ChangePasswordForm(FlaskForm):
    current_password = PasswordField('Current Password', validators=[
        DataRequired(message="Current password is required.")
    ])
    new_password = PasswordField('New Password', validators=[
        DataRequired(message="New password is required."),
        Length(min=6, message="New password must be at least 6 characters long.")
    ])
    confirm_password = PasswordField('Confirm New Password', validators=[
        DataRequired(message="Please confirm your new password."),
        EqualTo('new_password', message="Passwords must match.")
    ])
    submit = SubmitField('Update Password')
