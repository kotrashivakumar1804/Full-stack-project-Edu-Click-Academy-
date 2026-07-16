from datetime import datetime
from app.extensions import db

class Enrollment(db.Model):
    __tablename__ = 'enrollments'
    
    enrollment_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    student_id = db.Column(db.Integer, db.ForeignKey('students.student_id', ondelete='CASCADE'), nullable=False)
    course_id = db.Column(db.Integer, db.ForeignKey('courses.course_id', ondelete='CASCADE'), nullable=False)
    payment_status = db.Column(db.String(20), default='Unpaid')  # Unpaid, Submitted, Paid
    enrollment_status = db.Column(db.String(50), default='Pending Payment')  # Pending Payment, Payment Submitted, Approved, Rejected
    payment_reference = db.Column(db.String(100), nullable=True)  # Mock Txn ID / Receipt Reference
    payment_screenshot = db.Column(db.String(255), nullable=True)  # Path to uploaded payment screenshot
    discount_applied = db.Column(db.Float, nullable=True, default=None)   # e.g. 30.0 for 30% off
    final_fee = db.Column(db.Float, nullable=True, default=None)           # Actual fee paid after discount
    enrollment_date = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f"<Enrollment ID {self.enrollment_id} - Student ID {self.student_id} for Course ID {self.course_id}>"
