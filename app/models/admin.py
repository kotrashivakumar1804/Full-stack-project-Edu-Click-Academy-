from flask_login import UserMixin
from app.extensions import db

class Admin(db.Model, UserMixin):
    __tablename__ = 'admin'
    
    admin_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(100), unique=True, nullable=False, index=True)
    password = db.Column(db.String(255), nullable=False)

    def get_id(self):
        # Override Flask-Login get_id to return admin_id
        return str(self.admin_id)
        
    def __repr__(self):
        return f"<Admin {self.name} ({self.email})>"
