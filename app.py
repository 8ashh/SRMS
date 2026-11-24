import os
from flask import Flask, render_template
from config import Config
from extensions import db
from models import User, Student, Subject, Mark, Attendance, AuditLog
from routes.auth import auth_bp
from routes.admin import admin_bp
from routes.faculty import faculty_bp
from routes.student import student_bp
from routes.reports import reports_bp

def create_app(config_class=Config):
    """
    Application factory for Academic Performance Analytics & Student Record Management System (SRMS).
    MITS Gwalior.
    """
    app = Flask(__name__)
    app.config.from_object(config_class)

    # Initialize extensions
    db.init_app(app)

    # Register blueprints
    app.register_blueprint(auth_bp)
    app.register_blueprint(admin_bp)
    app.register_blueprint(faculty_bp)
    app.register_blueprint(student_bp)
    app.register_blueprint(reports_bp)

    # Global template context processor
    @app.context_processor
    def inject_global_vars():
        return {
            'INSTITUTION_NAME': app.config.get('INSTITUTION_NAME', 'Madhav Institute of Technology & Science, Gwalior'),
            'SYSTEM_NAME': app.config.get('SYSTEM_NAME', 'SRMS'),
            'DEPARTMENT': app.config.get('DEPARTMENT', 'Department of Computer Science & Engineering'),
            'PASSING_PERCENTAGE': app.config.get('PASSING_PERCENTAGE', 40.0),
            'ATTENDANCE_WARNING_THRESHOLD': app.config.get('ATTENDANCE_WARNING_THRESHOLD', 75.0),
        }

    # Error Handlers
    @app.errorhandler(403)
    def forbidden_error(error):
        return render_template('errors/403.html'), 403

    @app.errorhandler(404)
    def not_found_error(error):
        return render_template('errors/404.html'), 404

    @app.errorhandler(500)
    def internal_error(error):
        db.session.rollback()
        return render_template('errors/500.html'), 500

    # CLI command: initialize database tables
    @app.cli.command('init-db')
    def init_db_command():
        """Initialize database tables."""
        with app.app_context():
            db.create_all()
            print("Database tables initialized successfully.")

    return app

if __name__ == '__main__':
    app = create_app()
    with app.app_context():
        db.create_all()
    app.run(host='0.0.0.0', port=5001, debug=True)
