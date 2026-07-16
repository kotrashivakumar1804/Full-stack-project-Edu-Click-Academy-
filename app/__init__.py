import os
# pyrefly: ignore [missing-import]
from flask import Flask, session
from config import Config
from app.extensions import db, login_manager, csrf

def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)
    
    # Initialize Extensions
    db.init_app(app)
    login_manager.init_app(app)
    csrf.init_app(app)
    
    # Configure Login Manager
    login_manager.login_view = 'auth.login'
    login_manager.login_message_category = 'warning'
    
    @login_manager.user_loader
    def load_user(user_id):
        from app.models.student import Student
        from app.models.admin import Admin
        role = session.get('role')
        if role == 'admin':
            return Admin.query.get(int(user_id))
        elif role == 'student':
            return Student.query.get(int(user_id))
        return None

    # Context processors to make common utilities available in Jinja templates
    @app.context_processor
    def inject_utilities():
        from app.models.notification import Notification
        from flask_login import current_user
        from datetime import datetime
        
        unread_notifications_count = 0
        if current_user and current_user.is_authenticated and session.get('role') == 'student':
            unread_notifications_count = Notification.query.filter_by(
                student_id=current_user.student_id, is_read=False
            ).count()
            
        return dict(
            current_year=datetime.utcnow().year,
            unread_notifications_count=unread_notifications_count
        )

    # Register Blueprints
    from app.routes import all_blueprints
    for blueprint, url_prefix in all_blueprints:
        app.register_blueprint(blueprint, url_prefix=url_prefix)
        
    # Database Initialization & Seeding
    with app.app_context():
        # Auto-create tables (works for both SQLite and MySQL if database exists)
        db.create_all()
        
        # Database Migrations (ensure new fields and tables exist)
        from app.models.inquiry import Inquiry
        try:
            # Check/Add start_at in announcements
            db.session.execute(db.text("SELECT start_at FROM announcements LIMIT 1"))
        except Exception:
            db.session.rollback()
            try:
                db.session.execute(db.text("ALTER TABLE announcements ADD COLUMN start_at DATETIME NULL"))
                db.session.commit()
            except Exception as e:
                print(f"Migration error for start_at: {e}")
                db.session.rollback()

        try:
            # Check/Add login tracking columns in students
            db.session.execute(db.text("SELECT last_login FROM students LIMIT 1"))
        except Exception:
            db.session.rollback()
            try:
                db.session.execute(db.text("ALTER TABLE students ADD COLUMN last_login DATETIME NULL"))
                db.session.execute(db.text("ALTER TABLE students ADD COLUMN last_logout DATETIME NULL"))
                db.session.execute(db.text("ALTER TABLE students ADD COLUMN login_count INTEGER NOT NULL DEFAULT 0"))
                db.session.commit()
            except Exception as e:
                print(f"Migration error for student login columns: {e}")
                db.session.rollback()

        try:
            # Check/Add guest columns in inquiries
            db.session.execute(db.text("SELECT name FROM inquiries LIMIT 1"))
        except Exception:
            db.session.rollback()
            try:
                # Add columns
                db.session.execute(db.text("ALTER TABLE inquiries ADD COLUMN name VARCHAR(150) NULL"))
                db.session.execute(db.text("ALTER TABLE inquiries ADD COLUMN email VARCHAR(100) NULL"))
                db.session.execute(db.text("ALTER TABLE inquiries ADD COLUMN mobile VARCHAR(20) NULL"))
                db.session.commit()
            except Exception as e:
                print(f"Migration error for inquiries guest columns: {e}")
                db.session.rollback()

        # In SQLite, if inquiries.student_id or course_id was defined as NOT NULL, modify it to be NULL.
        is_sqlite = 'sqlite' in str(db.engine.url)
        if is_sqlite:
            try:
                columns = db.session.execute(db.text("PRAGMA table_info(inquiries)")).fetchall()
                student_id_info = [c for c in columns if c[1] == 'student_id']
                if student_id_info and student_id_info[0][3] == 1:
                    db.session.execute(db.text("PRAGMA foreign_keys=OFF"))
                    db.session.execute(db.text("ALTER TABLE inquiries RENAME TO inquiries_old"))
                    Inquiry.__table__.create(db.engine)
                    db.session.execute(db.text("""
                        INSERT INTO inquiries (inquiry_id, student_id, course_id, name, email, mobile, subject, message, status, created_at)
                        SELECT inquiry_id, student_id, course_id, NULL, NULL, NULL, subject, message, status, created_at
                        FROM inquiries_old
                    """))
                    db.session.execute(db.text("DROP TABLE inquiries_old"))
                    db.session.execute(db.text("PRAGMA foreign_keys=ON"))
                    db.session.commit()
            except Exception as e:
                print(f"SQLite inquiries migration error: {e}")
                db.session.rollback()
        else:
            try:
                db.session.execute(db.text("ALTER TABLE inquiries MODIFY student_id INT NULL"))
                db.session.execute(db.text("ALTER TABLE inquiries MODIFY course_id INT NULL"))
                db.session.commit()
            except Exception as e:
                print(f"MySQL inquiries migration error: {e}")
                db.session.rollback()
        
        # Check and Seed Administrator
        from app.models.admin import Admin
        from werkzeug.security import generate_password_hash
        
        admin_seeded = Admin.query.filter_by(email='admin@portal.com').first()
        if not admin_seeded:
            # Hash for Admin@123 password
            hashed_pw = generate_password_hash('Admin@123')
            admin_user = Admin(
                name="Portal Administrator",
                email="admin@portal.com",
                password=hashed_pw
            )
            db.session.add(admin_user)
            db.session.commit()
            
        # Check and Seed Default Courses
        from app.models.course import Course
        if Course.query.count() == 0:
            courses = [
                Course(
                    course_name="Introduction to Python Programming",
                    description="Learn the basics of Python, from syntax and control flows to object-oriented programming.",
                    duration="6 Weeks",
                    fee=3999.00,
                    instructor_name="Dr. Sarah Jenkins",
                    instructor_email="sarah.j@portal.com",
                    course_image="python_course.png",
                    status="Active"
                ),
                Course(
                    course_name="Full Stack Web Development",
                    description="Master HTML, CSS, JavaScript, Bootstrap, Flask, and Database deployments. Build complete web apps from scratch.",
                    duration="12 Weeks",
                    fee=5999.00,
                    instructor_name="Prof. Alex Mercer",
                    instructor_email="alex.m@portal.com",
                    course_image="webdev_course.png",
                    status="Active"
                ),
                Course(
                    course_name="Data Science and Machine Learning",
                    description="Dive deep into pandas, numpy, scikit-learn, and create your first prediction and classification models.",
                    duration="10 Weeks",
                    fee=5999.00,
                    instructor_name="Dr. Sarah Jenkins",
                    instructor_email="sarah.j@portal.com",
                    course_image="datascience_course.png",
                    status="Active"
                ),
                Course(
                    course_name="Cyber Security & Ethical Hacking",
                    description="Master cybersecurity fundamentals, firewall protection, risk assessment, and ethical hacking protocols.",
                    duration="8 Weeks",
                    fee=5999.00,
                    instructor_name="Dr. Alan Turing",
                    instructor_email="alan.t@portal.com",
                    course_image="cybersecurity_course.png",
                    status="Active"
                ),
                Course(
                    course_name="Cloud Computing & Architecture",
                    description="Deploy scalable infrastructure. Learn cloud architectures across AWS, Microsoft Azure, and Google Cloud.",
                    duration="10 Weeks",
                    fee=5999.00,
                    instructor_name="Prof. Alex Mercer",
                    instructor_email="alex.m@portal.com",
                    course_image="cloud_course.png",
                    status="Active"
                ),
                Course(
                    course_name="Mobile App Development (React Native)",
                    description="Build cross-platform iOS and Android mobile applications using React Native, styled interfaces, and web APIs.",
                    duration="8 Weeks",
                    fee=3999.00,
                    instructor_name="Prof. Alex Mercer",
                    instructor_email="alex.m@portal.com",
                    course_image="mobileapp_course.png",
                    status="Active"
                ),
                Course(
                    course_name="Artificial Intelligence & Deep Learning",
                    description="Dive deep into neural networks, natural language processing, computer vision, and cognitive AI model training.",
                    duration="12 Weeks",
                    fee=5999.00,
                    instructor_name="Dr. Sarah Jenkins",
                    instructor_email="sarah.j@portal.com",
                    course_image="ai_course.png",
                    status="Active"
                ),
                Course(
                    course_name="UI/UX Product Design",
                    description="Learn design system fundamentals, Figma prototyping, user flow research, and human-computer interactions.",
                    duration="6 Weeks",
                    fee=3999.00,
                    instructor_name="Dr. Grace Hopper",
                    instructor_email="grace.h@portal.com",
                    course_image="uiux_course.png",
                    status="Active"
                ),
                Course(
                    course_name="DevOps & CI/CD Pipelines",
                    description="Learn automated build deployment pipeline configurations using Docker, Kubernetes, Jenkins, and GitHub Actions.",
                    duration="8 Weeks",
                    fee=5999.00,
                    instructor_name="Dr. Alan Turing",
                    instructor_email="alan.t@portal.com",
                    course_image="devops_course.png",
                    status="Active"
                ),
                Course(
                    course_name="Database Systems & SQL",
                    description="Learn query optimization, relational normalization, index mapping, and transact schemas in PostgreSQL and MySQL.",
                    duration="6 Weeks",
                    fee=3999.00,
                    instructor_name="Dr. Grace Hopper",
                    instructor_email="grace.h@portal.com",
                    course_image="database_course.png",
                    status="Active"
                ),
                Course(
                    course_name="Agile & Scrum Project Management",
                    description="Coordinate modern product sprints, scrum workflows, team board metrics, and agile communication practices.",
                    duration="4 Weeks",
                    fee=3999.00,
                    instructor_name="Dr. Grace Hopper",
                    instructor_email="grace.h@portal.com",
                    course_image="agile_course.png",
                    status="Active"
                ),
                Course(
                    course_name="Digital Marketing Specialist",
                    description="Master search engine optimization, content tracking, google analytic dashboards, and social campaign strategies.",
                    duration="6 Weeks",
                    fee=3999.00,
                    instructor_name="Dr. Grace Hopper",
                    instructor_email="grace.h@portal.com",
                    course_image="digitalmarketing_course.png",
                    status="Active"
                )
            ]
            db.session.bulk_save_objects(courses)
            db.session.commit()
            
        # Check and Seed Default Announcement / Special Offer
        from app.models.announcement import Announcement
        if Announcement.query.count() == 0:
            ann = Announcement(
                title="Special Launch Offer - 50% Off!",
                description="Get flat 50% discount on all trending certification courses this week. Admissions are open!"
            )
            db.session.add(ann)
            db.session.commit()
            
    return app
