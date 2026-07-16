from app.routes.main import main_bp
from app.routes.auth import auth_bp
from app.routes.student import student_bp
from app.routes.admin import admin_bp

# Group all blueprints for easy registration in the app factory
all_blueprints = [
    (main_bp, ''),
    (auth_bp, ''),
    (student_bp, '/student'),
    (admin_bp, '/admin')
]
