from flask_wtf import FlaskForm
from wtforms import StringField, TextAreaField, SubmitField, SelectField
from wtforms.validators import DataRequired, Email, Length, Optional, Regexp

class ContactForm(FlaskForm):
    name = StringField('Your Name', validators=[
        DataRequired(message="Please enter your name."),
        Length(min=2, max=100)
    ])
    email = StringField('Email Address', validators=[
        DataRequired(message="Please enter your email."),
        Email(message="Invalid email address format.")
    ])
    subject = StringField('Subject', validators=[
        DataRequired(message="Subject is required."),
        Length(min=5, max=150)
    ])
    message = TextAreaField('Your Message', validators=[
        DataRequired(message="Message content is required."),
        Length(min=10, message="Message must be at least 10 characters long.")
    ])
    submit = SubmitField('Send Message')


class CourseInquiryForm(FlaskForm):
    message = TextAreaField('Inquiry / Discussion Message', validators=[
        DataRequired(message="Please enter a message to discuss your enrollment and request payment details."),
        Length(min=10, message="Inquiry message must be at least 10 characters long.")
    ])
    submit = SubmitField('Submit Contact Inquiry')


class InquiryCreateForm(FlaskForm):
    course_id = SelectField('Select Course', coerce=int, validators=[DataRequired()])
    subject = StringField('Subject', validators=[
        DataRequired(message="Subject is required."),
        Length(min=5, max=200)
    ])
    message = TextAreaField('Your Message', validators=[
        DataRequired(message="Please describe your inquiry."),
        Length(min=10, message="Message must be at least 10 characters.")
    ])
    submit = SubmitField('Submit Inquiry')


class AdminReplyForm(FlaskForm):
    reply_message = TextAreaField('Reply Message', validators=[
        DataRequired(message="Reply message cannot be empty.")
    ])
    submit = SubmitField('Send Reply')


class PublicInquiryForm(FlaskForm):
    name = StringField('Your Name', validators=[
        DataRequired(message="Please enter your name."),
        Length(min=2, max=100)
    ])
    email = StringField('Email Address', validators=[
        DataRequired(message="Please enter your email."),
        Email(message="Invalid email address format.")
    ])
    mobile = StringField('Mobile Number', validators=[
        DataRequired(message="Please enter your mobile number."),
        Regexp(r'^\+?[0-9\s\-()]{10,20}$', message="Invalid mobile number format.")
    ])
    course_id = SelectField('Select Course (Optional)', coerce=int, validators=[Optional()])
    subject = StringField('Subject', validators=[
        DataRequired(message="Subject is required."),
        Length(min=5, max=150)
    ])
    message = TextAreaField('Your Message', validators=[
        DataRequired(message="Message content is required."),
        Length(min=10, message="Message must be at least 10 characters long.")
    ])
    submit = SubmitField('Submit Inquiry')

