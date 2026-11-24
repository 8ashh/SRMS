from datetime import datetime, date
from flask import current_app
from extensions import db
from models import Attendance, Student, Subject
from services.audit_service import AuditService

class AttendanceService:
    @staticmethod
    def get_all(student_id=None, subject_id=None, att_date=None, page=1, per_page=25):
        """Fetch attendance records with filters."""
        query = Attendance.query.join(Student).join(Subject)

        if student_id:
            query = query.filter(Attendance.student_id == student_id)
        if subject_id:
            query = query.filter(Attendance.subject_id == subject_id)
        if att_date:
            if isinstance(att_date, str):
                try:
                    att_date = datetime.strptime(att_date, '%Y-%m-%d').date()
                except ValueError:
                    pass
            query = query.filter(Attendance.date == att_date)

        query = query.order_by(Attendance.date.desc(), Student.roll_no.asc())

        if page and per_page:
            return query.paginate(page=page, per_page=per_page, error_out=False)
        return query.all()

    @staticmethod
    def get_by_id(att_id):
        return Attendance.query.get(att_id)

    @staticmethod
    def record_attendance(student_id, subject_id, att_date, status):
        """Record or update a single attendance record."""
        student = Student.query.get(student_id)
        if not student:
            return None, "Selected student does not exist."

        subject = Subject.query.get(subject_id)
        if not subject:
            return None, "Selected subject does not exist."

        valid, err = Attendance.validate_attendance(status, att_date)
        if not valid:
            return None, err

        if isinstance(att_date, str):
            att_date = datetime.strptime(att_date, '%Y-%m-%d').date()

        # Check existing
        existing = Attendance.query.filter_by(student_id=student_id, subject_id=subject_id, date=att_date).first()
        if existing:
            # Update status if different
            if existing.status != status:
                old_status = existing.status
                existing.status = status
                db.session.commit()
                AuditService.log(
                    action="UPDATE_ATTENDANCE",
                    module="Attendance",
                    record_id=existing.att_id,
                    description=f"Updated attendance for '{student.name}' in '{subject.code}' on {att_date} from {old_status} to {status}."
                )
            return existing, ""

        try:
            att = Attendance(
                student_id=student_id,
                subject_id=subject_id,
                date=att_date,
                status=status
            )
            db.session.add(att)
            db.session.commit()

            AuditService.log(
                action="RECORD_ATTENDANCE",
                module="Attendance",
                record_id=att.att_id,
                description=f"Recorded '{status}' attendance for '{student.name}' ({student.roll_no}) in '{subject.code}' on {att_date}."
            )
            return att, ""
        except Exception as e:
            db.session.rollback()
            return None, f"Failed to record attendance: {str(e)}"

    @staticmethod
    def record_batch_attendance(subject_id, att_date, student_status_dict):
        """
        Record attendance for a whole class batch.
        student_status_dict: {student_id: 'Present'|'Absent'}
        """
        subject = Subject.query.get(subject_id)
        if not subject:
            return False, "Selected subject does not exist."

        if isinstance(att_date, str):
            try:
                att_date = datetime.strptime(att_date, '%Y-%m-%d').date()
            except ValueError:
                return False, "Invalid date format."

        if att_date > date.today():
            return False, "Future attendance dates are not permitted."

        success_count = 0
        try:
            for s_id_str, status in student_status_dict.items():
                s_id = int(s_id_str)
                if status not in ('Present', 'Absent'):
                    continue

                existing = Attendance.query.filter_by(student_id=s_id, subject_id=subject_id, date=att_date).first()
                if existing:
                    existing.status = status
                else:
                    new_att = Attendance(
                        student_id=s_id,
                        subject_id=subject_id,
                        date=att_date,
                        status=status
                    )
                    db.session.add(new_att)
                success_count += 1

            db.session.commit()

            AuditService.log(
                action="BATCH_ATTENDANCE",
                module="Attendance",
                description=f"Marked attendance for {success_count} students in '{subject.code}' for date {att_date}."
            )
            return True, f"Successfully recorded attendance for {success_count} students."
        except Exception as e:
            db.session.rollback()
            return False, f"Failed to record batch attendance: {str(e)}"

    @staticmethod
    def calculate_student_attendance(student_id, subject_id=None):
        """
        Calculates total, present, absent count, percentage and risk badge for a student.
        """
        query = Attendance.query.filter_by(student_id=student_id)
        if subject_id:
            query = query.filter_by(subject_id=subject_id)

        records = query.all()
        total = len(records)
        if total == 0:
            return {
                'total': 0,
                'present': 0,
                'absent': 0,
                'percentage': 0.0,
                'badge_class': 'secondary',
                'status_label': 'No Records'
            }

        present = sum(1 for r in records if r.status == 'Present')
        absent = total - present
        percentage = round((present / total) * 100.0, 2)

        # Thresholds
        warning_thresh = current_app.config.get('ATTENDANCE_WARNING_THRESHOLD', 75.0) if current_app else 75.0
        critical_thresh = current_app.config.get('ATTENDANCE_CRITICAL_THRESHOLD', 60.0) if current_app else 60.0

        if percentage >= warning_thresh:
            badge_class = 'success'
            status_label = 'Good'
        elif percentage >= critical_thresh:
            badge_class = 'warning'
            status_label = 'Attention'
        else:
            badge_class = 'danger'
            status_label = 'Low Attendance'

        return {
            'total': total,
            'present': present,
            'absent': absent,
            'percentage': percentage,
            'badge_class': badge_class,
            'status_label': status_label
        }

    @staticmethod
    def get_subject_attendance_summary(subject_id):
        """Get attendance summary for a given subject across all students."""
        records = Attendance.query.filter_by(subject_id=subject_id).all()
        total = len(records)
        if total == 0:
            return {'total': 0, 'present': 0, 'absent': 0, 'percentage': 0.0}
        present = sum(1 for r in records if r.status == 'Present')
        return {
            'total': total,
            'present': present,
            'absent': total - present,
            'percentage': round((present / total) * 100.0, 2)
        }
