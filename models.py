import re
from datetime import datetime, date
from werkzeug.security import generate_password_hash, check_password_hash
from extensions import db

class Student(db.Model):
    """
    Student entity representing enrolled students at MITS Gwalior.
    Indexed on roll_no for high-performance lookup.
    """
    __tablename__ = 'students'

    student_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    roll_no = db.Column(db.String(30), unique=True, nullable=False, index=True)
    name = db.Column(db.String(100), nullable=False)
    semester = db.Column(db.Integer, nullable=False, index=True)
    section = db.Column(db.String(10), nullable=False, index=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    # Relationships
    marks = db.relationship('Mark', backref='student', lazy='dynamic', cascade='all, delete-orphan')
    attendance_records = db.relationship('Attendance', backref='student', lazy='dynamic', cascade='all, delete-orphan')
    user = db.relationship('User', backref='student_profile', uselist=False, cascade='all, delete-orphan')

    @staticmethod
    def validate_roll_no(roll_no):
        if not roll_no or not str(roll_no).strip():
            return False, "Roll number is required."
        roll_cleaned = str(roll_no).strip()
        if not re.match(r'^[A-Za-z0-9]+$', roll_cleaned):
            return False, "Roll number must contain letters and digits only."
        return True, ""

    @staticmethod
    def validate_name(name):
        if not name or not str(name).strip():
            return False, "Student name is required."
        name_cleaned = str(name).strip()
        if len(name_cleaned) > 100:
            return False, "Name cannot exceed 100 characters."
        # Allow letters, spaces, dots, and hyphens (common in Indian names)
        if not re.match(r'^[A-Za-z\s\.\-]+$', name_cleaned):
            return False, "Name should contain letters and spaces only."
        return True, ""

    @staticmethod
    def validate_semester(sem):
        try:
            sem_val = int(sem)
            if 1 <= sem_val <= 8:
                return True, ""
            return False, "Semester must be a whole number between 1 and 8."
        except (ValueError, TypeError):
            return False, "Semester must be a valid integer."

    @staticmethod
    def validate_section(section):
        if not section or not str(section).strip():
            return False, "Section is required."
        return True, ""

    def to_dict(self):
        return {
            'student_id': self.student_id,
            'roll_no': self.roll_no,
            'name': self.name,
            'semester': self.semester,
            'section': self.section,
            'created_at': self.created_at.strftime('%Y-%m-%d %H:%M:%S') if self.created_at else None
        }


class Subject(db.Model):
    """
    Academic subject / course entity.
    Indexed on subject code for rapid lookups.
    """
    __tablename__ = 'subjects'

    subject_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    code = db.Column(db.String(20), unique=True, nullable=False, index=True)
    name = db.Column(db.String(100), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    # Relationships
    marks = db.relationship('Mark', backref='subject', lazy='dynamic', cascade='all, delete-orphan')
    attendance_records = db.relationship('Attendance', backref='subject', lazy='dynamic', cascade='all, delete-orphan')

    @staticmethod
    def validate_code(code):
        if not code or not str(code).strip():
            return False, "Subject code is required."
        clean_code = str(code).strip()
        if not re.match(r'^[A-Za-z0-9\-]+$', clean_code):
            return False, "Subject code must contain letters, digits, and hyphens only."
        return True, ""

    def to_dict(self):
        return {
            'subject_id': self.subject_id,
            'code': self.code,
            'name': self.name,
            'created_at': self.created_at.strftime('%Y-%m-%d %H:%M:%S') if self.created_at else None
        }


class Mark(db.Model):
    """
    Assessment score record.
    Prevents duplicate entries for the same student, subject, and test number.
    """
    __tablename__ = 'marks'

    mark_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    student_id = db.Column(db.Integer, db.ForeignKey('students.student_id', ondelete='CASCADE'), nullable=False, index=True)
    subject_id = db.Column(db.Integer, db.ForeignKey('subjects.subject_id', ondelete='CASCADE'), nullable=False, index=True)
    test_no = db.Column(db.Integer, nullable=False)
    score = db.Column(db.Float, nullable=False)
    max_score = db.Column(db.Float, nullable=False, default=100.0)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    # Unique constraint to prevent duplicate entry for same test
    __table_args__ = (
        db.UniqueConstraint('student_id', 'subject_id', 'test_no', name='uq_student_subject_test'),
    )

    @property
    def percentage(self):
        if self.max_score and self.max_score > 0:
            return round((self.score / self.max_score) * 100.0, 2)
        return 0.0

    @staticmethod
    def validate_marks(score, max_score, test_no):
        try:
            t_no = int(test_no)
            if t_no <= 0:
                return False, "Test number must be a positive integer."
        except (ValueError, TypeError):
            return False, "Test number must be a valid integer."

        try:
            sc = float(score)
            m_sc = float(max_score)
        except (ValueError, TypeError):
            return False, "Score and Maximum Score must be valid numbers."

        if sc < 0:
            return False, "Score cannot be negative."
        if m_sc <= 0:
            return False, "Maximum score must be greater than zero."
        if sc > m_sc:
            return False, "Score cannot exceed maximum score."

        return True, ""

    def to_dict(self):
        return {
            'mark_id': self.mark_id,
            'student_id': self.student_id,
            'student_name': self.student.name if self.student else None,
            'roll_no': self.student.roll_no if self.student else None,
            'subject_id': self.subject_id,
            'subject_code': self.subject.code if self.subject else None,
            'subject_name': self.subject.name if self.subject else None,
            'test_no': self.test_no,
            'score': self.score,
            'max_score': self.max_score,
            'percentage': self.percentage,
            'created_at': self.created_at.strftime('%Y-%m-%d %H:%M:%S') if self.created_at else None,
            'updated_at': self.updated_at.strftime('%Y-%m-%d %H:%M:%S') if self.updated_at else None
        }


class Attendance(db.Model):
    """
    Daily attendance tracking record per subject and student.
    Prevents duplicate attendance entries on the same date.
    """
    __tablename__ = 'attendance'

    att_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    student_id = db.Column(db.Integer, db.ForeignKey('students.student_id', ondelete='CASCADE'), nullable=False, index=True)
    subject_id = db.Column(db.Integer, db.ForeignKey('subjects.subject_id', ondelete='CASCADE'), nullable=False, index=True)
    date = db.Column(db.Date, nullable=False, index=True)
    status = db.Column(db.String(10), nullable=False)  # 'Present' or 'Absent'
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    __table_args__ = (
        db.UniqueConstraint('student_id', 'subject_id', 'date', name='uq_student_subject_date'),
    )

    @staticmethod
    def validate_attendance(status, att_date):
        if status not in ('Present', 'Absent'):
            return False, "Attendance status can only be 'Present' or 'Absent'."

        if not att_date:
            return False, "Date is required."

        if isinstance(att_date, str):
            try:
                att_date = datetime.strptime(att_date, '%Y-%m-%d').date()
            except ValueError:
                return False, "Invalid date format. Expected YYYY-MM-DD."

        if att_date > date.today():
            return False, "Future attendance dates are not permitted."

        return True, ""

    def to_dict(self):
        return {
            'att_id': self.att_id,
            'student_id': self.student_id,
            'student_name': self.student.name if self.student else None,
            'roll_no': self.student.roll_no if self.student else None,
            'subject_id': self.subject_id,
            'subject_code': self.subject.code if self.subject else None,
            'subject_name': self.subject.name if self.subject else None,
            'date': self.date.strftime('%Y-%m-%d') if self.date else None,
            'status': self.status,
            'created_at': self.created_at.strftime('%Y-%m-%d %H:%M:%S') if self.created_at else None
        }


class User(db.Model):
    """
    User authentication model with RBAC (admin, faculty, student).
    Passwords securely hashed with pbkdf2/scrypt via Werkzeug.
    """
    __tablename__ = 'users'

    user_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    username = db.Column(db.String(50), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(256), nullable=False)
    role = db.Column(db.String(20), nullable=False)  # 'admin', 'faculty', 'student'
    student_id = db.Column(db.Integer, db.ForeignKey('students.student_id', ondelete='CASCADE'), nullable=True)
    faculty_name = db.Column(db.String(100), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password, method='pbkdf2:sha256')

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def is_admin(self):
        return self.role == 'admin'

    def is_faculty(self):
        return self.role == 'faculty'

    def is_student(self):
        return self.role == 'student'

    def to_dict(self):
        return {
            'user_id': self.user_id,
            'username': self.username,
            'role': self.role,
            'student_id': self.student_id,
            'faculty_name': self.faculty_name,
            'created_at': self.created_at.strftime('%Y-%m-%d %H:%M:%S') if self.created_at else None
        }


class AuditLog(db.Model):
    """
    Immutable activity logging for administrative auditing.
    Records who did what, when, and to which module.
    """
    __tablename__ = 'audit_logs'

    log_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.user_id', ondelete='SET NULL'), nullable=True)
    action = db.Column(db.String(50), nullable=False)
    module = db.Column(db.String(50), nullable=False)
    record_id = db.Column(db.String(50), nullable=True)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow, nullable=False, index=True)
    description = db.Column(db.Text, nullable=False)

    user = db.relationship('User', backref='logs')

    def to_dict(self):
        return {
            'log_id': self.log_id,
            'user_id': self.user_id,
            'username': self.user.username if self.user else 'System',
            'action': self.action,
            'module': self.module,
            'record_id': self.record_id,
            'timestamp': self.timestamp.strftime('%Y-%m-%d %H:%M:%S') if self.timestamp else None,
            'description': self.description
        }
