import os

BASE_DIR = os.path.abspath(os.path.dirname(__file__))
INSTANCE_DIR = os.path.join(BASE_DIR, 'instance')
os.makedirs(INSTANCE_DIR, exist_ok=True)

class Config:
    """Base application configuration."""
    SECRET_KEY = os.environ.get('SECRET_KEY', 'mits-srms-secret-key-2026-secure-session')
    SQLALCHEMY_DATABASE_URI = os.environ.get(
        'DATABASE_URL', 
        f"sqlite:///{os.path.join(INSTANCE_DIR, 'database.db')}"
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # Institution & System Branding
    INSTITUTION_NAME = "Madhav Institute of Technology & Science (MITS), Gwalior"
    SYSTEM_NAME = "Academic Performance Analytics & Student Record Management System"
    DEPARTMENT = "Department of Computer Science & Engineering"
    
    # Configurable Academic Thresholds
    ATTENDANCE_WARNING_THRESHOLD = float(os.environ.get('ATTENDANCE_WARNING_THRESHOLD', 75.0))
    ATTENDANCE_CRITICAL_THRESHOLD = float(os.environ.get('ATTENDANCE_CRITICAL_THRESHOLD', 60.0))
    PASSING_PERCENTAGE = float(os.environ.get('PASSING_PERCENTAGE', 40.0))
    
    # Configurable Grade Cutoffs (Percentage >= cutoff)
    GRADE_CUTOFFS = {
        'A': 75.0,
        'B': 60.0,
        'C': 40.0,
        'F': 0.0
    }
    
    # Anomaly Detection Defaults
    Z_SCORE_THRESHOLD = -1.5
    PERFORMANCE_DROP_THRESHOLD = 15.0  # 15% drop compared to previous test

class TestConfig(Config):
    """Configuration for testing with an in-memory/isolated SQLite database."""
    TESTING = True
    WTF_CSRF_ENABLED = False
    SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'
