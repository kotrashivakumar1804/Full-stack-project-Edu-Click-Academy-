from datetime import datetime
from flask_login import UserMixin
from app.extensions import db

class Student(db.Model, UserMixin):
    __tablename__ = 'students'
    
    student_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    full_name = db.Column(db.String(150), nullable=False)
    email = db.Column(db.String(100), unique=True, nullable=False, index=True)
    mobile = db.Column(db.String(20), nullable=False)
    password = db.Column(db.String(255), nullable=False)
    date_of_birth = db.Column(db.Date, nullable=False, default=lambda: datetime.strptime("2000-01-01", "%Y-%m-%d").date())
    gender = db.Column(db.String(10), nullable=False)
    profile_picture = db.Column(db.String(255), default='default_profile.png')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Activity tracking columns
    last_login = db.Column(db.DateTime, nullable=True, default=None)
    last_logout = db.Column(db.DateTime, nullable=True, default=None)
    login_count = db.Column(db.Integer, nullable=False, default=0)
    
    # Relationships
    enrollments = db.relationship('Enrollment', backref='student', lazy=True, cascade="all, delete-orphan")
    notifications = db.relationship('Notification', backref='student', lazy=True, cascade="all, delete-orphan")

    def get_id(self):
        # Override Flask-Login get_id to return student_id
        return str(self.student_id)
        
    def __repr__(self):
        return f"<Student {self.full_name} ({self.email})>"
