from datetime import datetime
from app.extensions import db

# Join table for many-to-many relationship between Announcements (Offers) and Courses
offer_courses = db.Table('offer_courses',
    db.Column('announcement_id', db.Integer, db.ForeignKey('announcements.announcement_id', ondelete='CASCADE'), primary_key=True),
    db.Column('course_id', db.Integer, db.ForeignKey('courses.course_id', ondelete='CASCADE'), primary_key=True)
)

class Announcement(db.Model):
    __tablename__ = 'announcements'
    
    announcement_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text, nullable=False)
    discount_percent = db.Column(db.Float, nullable=True, default=None)   # e.g. 30.0 for 30% off
    is_offer = db.Column(db.Boolean, default=False)                        # True if it's a discount offer
    is_active = db.Column(db.Boolean, default=True)                        # Toggle active/inactive
    start_at = db.Column(db.DateTime, nullable=True, default=None)         # None = starts immediately
    expires_at = db.Column(db.DateTime, nullable=True, default=None)       # None = never expires
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Relationship to Courses
    courses = db.relationship('Course', secondary=offer_courses, backref=db.backref('offers', lazy='dynamic'))

    @property
    def is_valid_offer(self):
        """Returns True if this is an active, non-expired offer with a discount."""
        if not self.is_offer or not self.is_active or self.discount_percent is None:
            return False
        now = datetime.utcnow()
        if self.start_at and self.start_at > now:
            return False
        if self.expires_at and self.expires_at < now:
            return False
        return True

    def __repr__(self):
        return f"<Announcement '{self.title}' on {self.created_at.strftime('%Y-%m-%d')}>"
