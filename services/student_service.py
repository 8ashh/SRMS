from datetime import datetime
from sqlalchemy import or_
from extensions import db
from models import Student, User, Mark, Attendance
from services.audit_service import AuditService

class StudentService:
    @staticmethod
    def get_all(search=None, semester=None, section=None, page=1, per_page=20):
        """Fetch students with optional search, filters, and pagination."""
        query = Student.query
        
        if search:
            search_term = f"%{search.strip()}%"
            query = query.filter(
                or_(
                    Student.name.ilike(search_term),
                    Student.roll_no.ilike(search_term)
                )
            )
        
        if semester:
            try:
                sem_val = int(semester)
                query = query.filter(Student.semester == sem_val)
            except (ValueError, TypeError):
                pass
                
        if section:
            query = query.filter(Student.section == section.strip())

        query = query.order_by(Student.roll_no.asc())
        
        if page and per_page:
            return query.paginate(page=page, per_page=per_page, error_out=False)
        return query.all()

    @staticmethod
    def get_by_id(student_id):
        """Retrieve single student by primary key."""
        return Student.query.get(student_id)

    @staticmethod
    def get_by_roll_no(roll_no):
        """Retrieve single student by unique roll number."""
        if not roll_no:
            return None
        return Student.query.filter_by(roll_no=roll_no.strip().upper()).first()

    @staticmethod
    def create_student(roll_no, name, semester, section, create_user_account=True, default_password=None):
        """
        Validate and create a new student record.
        Optionally provisions a linked Student login account.
        """
        roll_clean = str(roll_no).strip().upper() if roll_no else ''
        name_clean = str(name).strip() if name else ''
        section_clean = str(section).strip().upper() if section else ''

        # 1. Validation
        valid_roll, err_roll = Student.validate_roll_no(roll_clean)
        if not valid_roll:
            return None, err_roll

        valid_name, err_name = Student.validate_name(name_clean)
        if not valid_name:
            return None, err_name

        valid_sem, err_sem = Student.validate_semester(semester)
        if not valid_sem:
            return None, err_sem

        valid_sec, err_sec = Student.validate_section(section_clean)
        if not valid_sec:
            return None, err_sec

        # Check uniqueness
        if Student.query.filter_by(roll_no=roll_clean).first():
            return None, f"A student with Roll Number '{roll_clean}' already exists."

        try:
            student = Student(
                roll_no=roll_clean,
                name=name_clean,
                semester=int(semester),
                section=section_clean
            )
            db.session.add(student)
            db.session.flush()  # Generate student_id

            # Create student user account if requested
            if create_user_account:
                # Check if username is taken
                username = roll_clean.lower()
                pwd = default_password if default_password else f"{roll_clean}@123"
                
                existing_user = User.query.filter_by(username=username).first()
                if not existing_user:
                    user = User(
                        username=username,
                        role='student',
                        student_id=student.student_id
                    )
                    user.set_password(pwd)
                    db.session.add(user)

            db.session.commit()

            AuditService.log(
                action="ADD_STUDENT",
                module="Students",
                record_id=student.student_id,
                description=f"Added student '{student.name}' with Roll No '{student.roll_no}' (Sem {student.semester}-{student.section})."
            )
            return student, ""
        except Exception as e:
            db.session.rollback()
            return None, f"Failed to create student: {str(e)}"

    @staticmethod
    def update_student(student_id, roll_no, name, semester, section):
        """Validate and update existing student."""
        student = Student.query.get(student_id)
        if not student:
            return None, "Student record not found."

        roll_clean = str(roll_no).strip().upper() if roll_no else ''
        name_clean = str(name).strip() if name else ''
        section_clean = str(section).strip().upper() if section else ''

        valid_roll, err_roll = Student.validate_roll_no(roll_clean)
        if not valid_roll:
            return None, err_roll

        valid_name, err_name = Student.validate_name(name_clean)
        if not valid_name:
            return None, err_name

        valid_sem, err_sem = Student.validate_semester(semester)
        if not valid_sem:
            return None, err_sem

        valid_sec, err_sec = Student.validate_section(section_clean)
        if not valid_sec:
            return None, err_sec

        # Check roll_no conflict
        conflict = Student.query.filter(Student.roll_no == roll_clean, Student.student_id != student_id).first()
        if conflict:
            return None, f"Roll Number '{roll_clean}' is already assigned to another student."

        try:
            old_desc = f"{student.name} ({student.roll_no})"
            student.roll_no = roll_clean
            student.name = name_clean
            student.semester = int(semester)
            student.section = section_clean

            # If student has a user account, update username if it matched roll_no
            if student.user:
                student.user.username = roll_clean.lower()

            db.session.commit()

            AuditService.log(
                action="UPDATE_STUDENT",
                module="Students",
                record_id=student.student_id,
                description=f"Updated student record for '{old_desc}' to '{student.name}' ({student.roll_no})."
            )
            return student, ""
        except Exception as e:
            db.session.rollback()
            return None, f"Failed to update student: {str(e)}"

    @staticmethod
    def delete_student(student_id):
        """Delete student and all associated records."""
        student = Student.query.get(student_id)
        if not student:
            return False, "Student not found."

        try:
            info = f"{student.name} ({student.roll_no})"
            db.session.delete(student)
            db.session.commit()

            AuditService.log(
                action="DELETE_STUDENT",
                module="Students",
                record_id=student_id,
                description=f"Deleted student record for '{info}' along with associated marks and attendance."
            )
            return True, ""
        except Exception as e:
            db.session.rollback()
            return False, f"Failed to delete student: {str(e)}"
