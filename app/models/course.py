from app.extensions import db

class Course(db.Model):
    __tablename__ = 'courses'
    
    course_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    course_name = db.Column(db.String(150), nullable=False)
    description = db.Column(db.Text, nullable=False)
    duration = db.Column(db.String(50), nullable=False)
    fee = db.Column(db.Numeric(10, 2), nullable=False)
    instructor_name = db.Column(db.String(100), nullable=False)
    instructor_email = db.Column(db.String(100), nullable=False)
    course_image = db.Column(db.String(255), default='default_course.png')
    status = db.Column(db.String(10), default='Active')  # Active or Inactive
    
    # Relationships
    enrollments = db.relationship('Enrollment', backref='course', lazy=True, cascade="all, delete-orphan")

    @property
    def active_offer(self):
        valid_offers = [o for o in self.offers if o.is_valid_offer]
        
        # Fallback to global offers (active offers with no specific courses assigned)
        from app.models.announcement import Announcement
        global_offers = Announcement.query.filter_by(is_offer=True, is_active=True).all()
        for o in global_offers:
            if o.is_valid_offer and len(o.courses) == 0:
                valid_offers.append(o)
                
        if not valid_offers:
            return None
        return max(valid_offers, key=lambda x: x.discount_percent)

    @property
    def current_price_details(self):
        offer = self.active_offer
        if offer:
            discounted_fee = round(float(self.fee) * (1 - float(offer.discount_percent) / 100), 2)
            discount_amount = round(float(self.fee) * float(offer.discount_percent) / 100, 2)
            return {
                'has_offer': True,
                'discount_percent': offer.discount_percent,
                'original_fee': float(self.fee),
                'discounted_fee': discounted_fee,
                'discount_amount': discount_amount,
                'offer': offer
            }
        return {
            'has_offer': False,
            'discount_percent': 0,
            'original_fee': float(self.fee),
            'discounted_fee': float(self.fee),
            'discount_amount': 0,
            'offer': None
        }

    def __repr__(self):
        return f"<Course {self.course_name} by {self.instructor_name}>"
