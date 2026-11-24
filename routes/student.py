from flask import Blueprint, render_template, session, flash, redirect, url_for
from models import Student, Mark, Attendance
from routes.auth import role_required
from services.marks_service import MarksService
from services.attendance_service import AttendanceService
from services.analytics_service import AnalyticsService
from services.anomaly_service import AnomalyService
from services.prediction_service import PredictionService

student_bp = Blueprint('student', __name__, url_prefix='/student')

@student_bp.before_request
@role_required(['student'])
def before_request():
    pass

def get_current_student():
    student_id = session.get('student_id')
    if not student_id:
        return None
    return Student.query.get(student_id)

@student_bp.route('/dashboard')
def dashboard():
    student = get_current_student()
    if not student:
        flash("Student profile not linked to this account. Please contact the administrator.", "danger")
        return render_template('student/no_profile.html')

    marks = MarksService.get_student_marks(student.student_id)
    att_info = AttendanceService.calculate_student_attendance(student.student_id)
    alerts = AnomalyService.get_student_alerts(student.student_id)
    prediction = PredictionService.predict_for_student(student.student_id)
    analytics = AnalyticsService.get_individual_student_analytics(student.student_id)

    return render_template(
        'student/dashboard.html',
        student=student,
        marks=marks,
        att_info=att_info,
        alerts=alerts,
        prediction=prediction,
        analytics=analytics
    )

@student_bp.route('/profile')
def profile():
    student = get_current_student()
    if not student:
        flash("Student profile not linked.", "danger")
        return redirect(url_for('student.dashboard'))

    att_info = AttendanceService.calculate_student_attendance(student.student_id)
    return render_template('student/profile.html', student=student, att_info=att_info)

@student_bp.route('/marks')
def marks():
    student = get_current_student()
    if not student:
        flash("Student profile not linked.", "danger")
        return redirect(url_for('student.dashboard'))

    marks_list = MarksService.get_student_marks(student.student_id)
    analytics = AnalyticsService.get_individual_student_analytics(student.student_id)
    return render_template('student/marks.html', student=student, marks=marks_list, analytics=analytics)

@student_bp.route('/attendance')
def attendance():
    student = get_current_student()
    if not student:
        flash("Student profile not linked.", "danger")
        return redirect(url_for('student.dashboard'))

    records = Attendance.query.filter_by(student_id=student.student_id).order_by(Attendance.date.desc()).all()
    att_info = AttendanceService.calculate_student_attendance(student.student_id)
    return render_template('student/attendance.html', student=student, records=records, att_info=att_info)

@student_bp.route('/performance')
def performance():
    student = get_current_student()
    if not student:
        flash("Student profile not linked.", "danger")
        return redirect(url_for('student.dashboard'))

    analytics = AnalyticsService.get_individual_student_analytics(student.student_id)
    alerts = AnomalyService.get_student_alerts(student.student_id)
    return render_template('student/performance.html', student=student, analytics=analytics, alerts=alerts)

@student_bp.route('/predictions')
def predictions():
    student = get_current_student()
    if not student:
        flash("Student profile not linked.", "danger")
        return redirect(url_for('student.dashboard'))

    prediction = PredictionService.predict_for_student(student.student_id)
    return render_template('student/predictions.html', student=student, prediction=prediction)
