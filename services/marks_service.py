from datetime import datetime
from extensions import db
from models import Mark, Student, Subject
from services.audit_service import AuditService

class MarksService:
    @staticmethod
    def get_all(student_id=None, subject_id=None, semester=None, test_no=None, page=1, per_page=25):
        """Fetch marks with filters and pagination."""
        query = Mark.query.join(Student).join(Subject)

        if student_id:
            query = query.filter(Mark.student_id == student_id)
        if subject_id:
            query = query.filter(Mark.subject_id == subject_id)
        if semester:
            try:
                sem_val = int(semester)
                query = query.filter(Student.semester == sem_val)
            except (ValueError, TypeError):
                pass
        if test_no:
            try:
                t_val = int(test_no)
                query = query.filter(Mark.test_no == t_val)
            except (ValueError, TypeError):
                pass

        query = query.order_by(Student.roll_no.asc(), Mark.subject_id.asc(), Mark.test_no.asc())

        if page and per_page:
            return query.paginate(page=page, per_page=per_page, error_out=False)
        return query.all()

    @staticmethod
    def get_by_id(mark_id):
        return Mark.query.get(mark_id)

    @staticmethod
    def get_student_marks(student_id):
        """Retrieve all marks for a single student ordered by subject and test."""
        return Mark.query.filter_by(student_id=student_id).order_by(Mark.subject_id.asc(), Mark.test_no.asc()).all()

    @staticmethod
    def record_mark(student_id, subject_id, test_no, score, max_score=100.0):
        """
        Validate and record assessment score.
        Checks for duplicate entry for student + subject + test_no.
        """
        # Validate existence
        student = Student.query.get(student_id)
        if not student:
            return None, "Selected student does not exist."

        subject = Subject.query.get(subject_id)
        if not subject:
            return None, "Selected subject does not exist."

        # Validate numbers
        valid, err_msg = Mark.validate_marks(score, max_score, test_no)
        if not valid:
            return None, err_msg

        t_no = int(test_no)
        sc = round(float(score), 2)
        m_sc = round(float(max_score), 2)

        # Check duplicate
        existing = Mark.query.filter_by(student_id=student_id, subject_id=subject_id, test_no=t_no).first()
        if existing:
            return None, f"Mark entry for {student.name} ({subject.code} - Test {t_no}) already exists. Edit the existing record instead."

        try:
            mark = Mark(
                student_id=student_id,
                subject_id=subject_id,
                test_no=t_no,
                score=sc,
                max_score=m_sc
            )
            db.session.add(mark)
            db.session.commit()

            AuditService.log(
                action="RECORD_MARKS",
                module="Marks",
                record_id=mark.mark_id,
                description=f"Recorded Test {t_no} score ({sc}/{m_sc}, {mark.percentage}%) for student '{student.name}' ({student.roll_no}) in '{subject.code}'."
            )
            return mark, ""
        except Exception as e:
            db.session.rollback()
            return None, f"Failed to record mark: {str(e)}"

    @staticmethod
    def update_mark(mark_id, score, max_score, test_no=None):
        """Update an existing mark record with validation."""
        mark = Mark.query.get(mark_id)
        if not mark:
            return None, "Mark record not found."

        target_test_no = int(test_no) if test_no is not None else mark.test_no

        valid, err_msg = Mark.validate_marks(score, max_score, target_test_no)
        if not valid:
            return None, err_msg

        # If test_no changed, check conflict
        if target_test_no != mark.test_no:
            conflict = Mark.query.filter(
                Mark.student_id == mark.student_id,
                Mark.subject_id == mark.subject_id,
                Mark.test_no == target_test_no,
                Mark.mark_id != mark_id
            ).first()
            if conflict:
                return None, f"Another entry for Test {target_test_no} already exists for this student and subject."

        try:
            old_score = f"{mark.score}/{mark.max_score} (Test {mark.test_no})"
            mark.score = round(float(score), 2)
            mark.max_score = round(float(max_score), 2)
            mark.test_no = target_test_no
            mark.updated_at = datetime.utcnow()
            db.session.commit()

            AuditService.log(
                action="UPDATE_MARKS",
                module="Marks",
                record_id=mark.mark_id,
                description=f"Updated mark ID {mark.mark_id} from {old_score} to {mark.score}/{mark.max_score} (Test {mark.test_no}) for student '{mark.student.name}'."
            )
            return mark, ""
        except Exception as e:
            db.session.rollback()
            return None, f"Failed to update marks: {str(e)}"

    @staticmethod
    def delete_mark(mark_id):
        mark = Mark.query.get(mark_id)
        if not mark:
            return False, "Mark record not found."

        try:
            desc = f"Test {mark.test_no} score ({mark.score}/{mark.max_score}) for '{mark.student.name}' in '{mark.subject.code}'"
            db.session.delete(mark)
            db.session.commit()

            AuditService.log(
                action="DELETE_MARKS",
                module="Marks",
                record_id=mark_id,
                description=f"Deleted mark record: {desc}."
            )
            return True, ""
        except Exception as e:
            db.session.rollback()
            return False, f"Failed to delete mark record: {str(e)}"
