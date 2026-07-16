from datetime import datetime
from app.extensions import db

class Payment(db.Model):
    __tablename__ = 'payments'
    
    payment_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    enrollment_id = db.Column(db.Integer, db.ForeignKey('enrollments.enrollment_id', ondelete='CASCADE'), nullable=False)
    transaction_id = db.Column(db.String(100), nullable=False)
    payment_screenshot = db.Column(db.String(255), nullable=False)
    payment_date = db.Column(db.DateTime, default=datetime.utcnow)
    status = db.Column(db.String(20), default='Pending')  # 'Pending', 'Verified', 'Rejected'
    remarks = db.Column(db.Text, nullable=True)

    # Relationships
    enrollment = db.relationship('Enrollment', backref=db.backref('payments', lazy=True, cascade='all, delete-orphan'))

    def __repr__(self):
        return f"<Payment '{self.transaction_id}' status={self.status}>"
