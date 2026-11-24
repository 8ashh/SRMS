from extensions import db
from models import Subject
from services.audit_service import AuditService

class SubjectService:
    @staticmethod
    def get_all():
        """Retrieve all subjects ordered by code."""
        return Subject.query.order_by(Subject.code.asc()).all()

    @staticmethod
    def get_by_id(subject_id):
        return Subject.query.get(subject_id)

    @staticmethod
    def get_by_code(code):
        if not code:
            return None
        return Subject.query.filter_by(code=code.strip().upper()).first()

    @staticmethod
    def create_subject(code, name):
        code_clean = str(code).strip().upper() if code else ''
        name_clean = str(name).strip() if name else ''

        valid_code, err_code = Subject.validate_code(code_clean)
        if not valid_code:
            return None, err_code

        if not name_clean:
            return None, "Subject name is required."

        if Subject.query.filter_by(code=code_clean).first():
            return None, f"Subject code '{code_clean}' already exists."

        try:
            subject = Subject(code=code_clean, name=name_clean)
            db.session.add(subject)
            db.session.commit()

            AuditService.log(
                action="ADD_SUBJECT",
                module="Subjects",
                record_id=subject.subject_id,
                description=f"Created subject '{subject.name}' ({subject.code})."
            )
            return subject, ""
        except Exception as e:
            db.session.rollback()
            return None, f"Failed to create subject: {str(e)}"

    @staticmethod
    def update_subject(subject_id, code, name):
        subject = Subject.query.get(subject_id)
        if not subject:
            return None, "Subject not found."

        code_clean = str(code).strip().upper() if code else ''
        name_clean = str(name).strip() if name else ''

        valid_code, err_code = Subject.validate_code(code_clean)
        if not valid_code:
            return None, err_code

        if not name_clean:
            return None, "Subject name is required."

        conflict = Subject.query.filter(Subject.code == code_clean, Subject.subject_id != subject_id).first()
        if conflict:
            return None, f"Subject code '{code_clean}' is already assigned to another course."

        try:
            old_code = subject.code
            subject.code = code_clean
            subject.name = name_clean
            db.session.commit()

            AuditService.log(
                action="UPDATE_SUBJECT",
                module="Subjects",
                record_id=subject.subject_id,
                description=f"Updated subject '{old_code}' to '{subject.name}' ({subject.code})."
            )
            return subject, ""
        except Exception as e:
            db.session.rollback()
            return None, f"Failed to update subject: {str(e)}"

    @staticmethod
    def delete_subject(subject_id):
        subject = Subject.query.get(subject_id)
        if not subject:
            return False, "Subject not found."

        try:
            desc = f"{subject.name} ({subject.code})"
            db.session.delete(subject)
            db.session.commit()

            AuditService.log(
                action="DELETE_SUBJECT",
                module="Subjects",
                record_id=subject_id,
                description=f"Deleted subject '{desc}' and all associated marks and attendance."
            )
            return True, ""
        except Exception as e:
            db.session.rollback()
            return False, f"Failed to delete subject: {str(e)}"
