from datetime import date, timedelta
from services.attendance_service import AttendanceService

def test_attendance_recording_and_percentage(app, init_sample_data):
    with app.app_context():
        d1 = date.today() - timedelta(days=2)
        d2 = date.today() - timedelta(days=1)
        d3 = date.today()

        # Record 2 Present, 1 Absent for student 1 in subject 1 -> 66.67%
        AttendanceService.record_attendance(student_id=1, subject_id=1, att_date=d1, status='Present')
        AttendanceService.record_attendance(student_id=1, subject_id=1, att_date=d2, status='Present')
        AttendanceService.record_attendance(student_id=1, subject_id=1, att_date=d3, status='Absent')

        summary = AttendanceService.calculate_student_attendance(student_id=1, subject_id=1)
        assert summary['total'] == 3
        assert summary['present'] == 2
        assert summary['absent'] == 1
        assert summary['percentage'] == 66.67
        assert summary['badge_class'] == 'warning'  # 60-74% threshold

def test_future_attendance_date_rejection(app, init_sample_data):
    with app.app_context():
        future_date = date.today() + timedelta(days=5)
        att, err = AttendanceService.record_attendance(student_id=1, subject_id=1, att_date=future_date, status='Present')
        assert att is None
        assert "Future attendance dates" in err

def test_invalid_status_rejection(app, init_sample_data):
    with app.app_context():
        att, err = AttendanceService.record_attendance(student_id=1, subject_id=1, att_date=date.today(), status='Excused')
        assert att is None
        assert "Present" in err and "Absent" in err
