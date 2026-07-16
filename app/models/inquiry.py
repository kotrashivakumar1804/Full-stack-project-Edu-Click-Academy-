from datetime import datetime
from app.extensions import db

class Inquiry(db.Model):
    __tablename__ = 'inquiries'
    
    inquiry_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    student_id = db.Column(db.Integer, db.ForeignKey('students.student_id', ondelete='CASCADE'), nullable=True)
    course_id = db.Column(db.Integer, db.ForeignKey('courses.course_id', ondelete='CASCADE'), nullable=True)
    name = db.Column(db.String(150), nullable=True)
    email = db.Column(db.String(100), nullable=True)
    mobile = db.Column(db.String(20), nullable=True)
    subject = db.Column(db.String(200), nullable=False)
    message = db.Column(db.Text, nullable=False)
    status = db.Column(db.String(20), default='Pending')  # 'Pending', 'Replied', 'Closed'
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Relationships
    student = db.relationship('Student', backref=db.backref('inquiries', lazy=True, cascade='all, delete-orphan'))
    course = db.relationship('Course', backref=db.backref('inquiries', lazy=True, cascade='all, delete-orphan'))
    replies = db.relationship('InquiryReply', backref='inquiry', lazy=True, cascade='all, delete-orphan', order_by='InquiryReply.created_at')

    def __repr__(self):
        return f"<Inquiry '{self.subject}' status={self.status}>"


class InquiryReply(db.Model):
    __tablename__ = 'inquiry_replies'
    
    reply_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    inquiry_id = db.Column(db.Integer, db.ForeignKey('inquiries.inquiry_id', ondelete='CASCADE'), nullable=False)
    sender_role = db.Column(db.String(10), nullable=False)  # 'student' or 'admin'
    message = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f"<InquiryReply by {self.sender_role} on inquiry_id={self.inquiry_id}>"
