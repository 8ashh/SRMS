from datetime import datetime, date
from flask import Blueprint, render_template, request, redirect, url_for, flash
from extensions import db
from models import Student, Subject, Mark, Attendance
from routes.auth import role_required
from services.student_service import StudentService
from services.subject_service import SubjectService
from services.marks_service import MarksService
from services.attendance_service import AttendanceService
from services.analytics_service import AnalyticsService
from services.anomaly_service import AnomalyService
from services.prediction_service import PredictionService

faculty_bp = Blueprint('faculty', __name__, url_prefix='/faculty')

@faculty_bp.before_request
@role_required(['faculty'])
def before_request():
    pass

@faculty_bp.route('/dashboard')
def dashboard():
    summary = AnalyticsService.get_overall_summary()
    alerts = AnomalyService.detect_anomalies()
    high_risk_count = sum(1 for a in alerts if a['risk_level'] == 'High Risk')

    grade_dist = AnalyticsService.get_grade_distribution()
    subject_avg = AnalyticsService.get_subject_averages()
    trends = AnalyticsService.get_test_performance_trends()
    recent_marks = Mark.query.order_by(Mark.created_at.desc()).limit(5).all()

    return render_template(
        'faculty/dashboard.html',
        summary=summary,
        total_risk_count=len(alerts),
        high_risk_count=high_risk_count,
        grade_dist=grade_dist,
        subject_avg=subject_avg,
        trends=trends,
        recent_marks=recent_marks,
        top_alerts=alerts[:5]
    )

@faculty_bp.route('/students')
def students():
    search = request.args.get('search', '').strip()
    semester = request.args.get('semester', '').strip()
    section = request.args.get('section', '').strip()
    page = request.args.get('page', 1, type=int)

    pagination = StudentService.get_all(search=search, semester=semester, section=section, page=page, per_page=15)
    return render_template('faculty/students.html', pagination=pagination, search=search, semester=semester, section=section)

@faculty_bp.route('/students/<int:student_id>')
def student_profile(student_id):
    student = StudentService.get_by_id(student_id)
    if not student:
        flash("Student record not found.", "danger")
        return redirect(url_for('faculty.students'))

    marks = MarksService.get_student_marks(student_id)
    att_info = AttendanceService.calculate_student_attendance(student_id)
    alerts = AnomalyService.get_student_alerts(student_id)
    prediction = PredictionService.predict_for_student(student_id)
    analytics = AnalyticsService.get_individual_student_analytics(student_id)

    return render_template(
        'faculty/student_profile.html',
        student=student,
        marks=marks,
        att_info=att_info,
        alerts=alerts,
        prediction=prediction,
        analytics=analytics
    )

@faculty_bp.route('/subjects')
def subjects():
    subjects_list = SubjectService.get_all()
    return render_template('faculty/subjects.html', subjects=subjects_list)

@faculty_bp.route('/marks', methods=['GET', 'POST'])
def marks():
    if request.method == 'POST':
        student_id = request.form.get('student_id', type=int)
        subject_id = request.form.get('subject_id', type=int)
        test_no = request.form.get('test_no', type=int)
        score = request.form.get('score')
        max_score = request.form.get('max_score', 100.0)

        mark, err = MarksService.record_mark(student_id, subject_id, test_no, score, max_score)
        if err:
            flash(err, "danger")
        else:
            flash(f"Recorded Test {mark.test_no} score ({mark.score}/{mark.max_score}) successfully.", "success")
        return redirect(url_for('faculty.marks'))

    student_id = request.args.get('student_id', type=int)
    subject_id = request.args.get('subject_id', type=int)
    semester = request.args.get('semester')
    test_no = request.args.get('test_no', type=int)
    page = request.args.get('page', 1, type=int)

    pagination = MarksService.get_all(student_id=student_id, subject_id=subject_id, semester=semester, test_no=test_no, page=page, per_page=20)
    all_students = Student.query.order_by(Student.roll_no.asc()).all()
    all_subjects = SubjectService.get_all()

    return render_template(
        'faculty/marks.html',
        pagination=pagination,
        students=all_students,
        subjects=all_subjects,
        selected_student=student_id,
        selected_subject=subject_id,
        selected_sem=semester,
        selected_test=test_no
    )

@faculty_bp.route('/marks/edit/<int:mark_id>', methods=['POST'])
def edit_mark(mark_id):
    score = request.form.get('score')
    max_score = request.form.get('max_score')
    test_no = request.form.get('test_no')

    updated, err = MarksService.update_mark(mark_id, score, max_score, test_no)
    if err:
        flash(err, "danger")
    else:
        flash(f"Updated mark ID {mark_id} successfully.", "success")
    return redirect(request.referrer or url_for('faculty.marks'))

@faculty_bp.route('/attendance', methods=['GET', 'POST'])
def attendance():
    if request.method == 'POST':
        subject_id = request.form.get('subject_id', type=int)
        att_date = request.form.get('date')

        student_statuses = {}
        for key, val in request.form.items():
            if key.startswith('status_'):
                s_id = key.split('_')[1]
                student_statuses[s_id] = val

        success, msg = AttendanceService.record_batch_attendance(subject_id, att_date, student_statuses)
        if success:
            flash(msg, "success")
        else:
            flash(msg, "danger")
        return redirect(url_for('faculty.attendance', subject_id=subject_id, date=att_date))

    subject_id = request.args.get('subject_id', type=int)
    att_date = request.args.get('date', date.today().strftime('%Y-%m-%d'))
    student_id = request.args.get('student_id', type=int)
    page = request.args.get('page', 1, type=int)

    all_subjects = SubjectService.get_all()
    all_students = Student.query.order_by(Student.roll_no.asc()).all()

    current_statuses = {}
    if subject_id and att_date:
        records = Attendance.query.filter_by(subject_id=subject_id, date=datetime.strptime(att_date, '%Y-%m-%d').date()).all()
        for r in records:
            current_statuses[r.student_id] = r.status

    pagination = AttendanceService.get_all(student_id=student_id, subject_id=subject_id, att_date=att_date if not student_id else None, page=page, per_page=20)

    return render_template(
        'faculty/attendance.html',
        subjects=all_subjects,
        students=all_students,
        selected_subject=subject_id,
        selected_date=att_date,
        selected_student=student_id,
        current_statuses=current_statuses,
        pagination=pagination,
        today_date=date.today().strftime('%Y-%m-%d')
    )

@faculty_bp.route('/analytics')
def analytics():
    semester = request.args.get('semester')
    subject_id = request.args.get('subject_id', type=int)
    section = request.args.get('section')

    summary = AnalyticsService.get_overall_summary(semester=semester, section=section)
    subject_avg = AnalyticsService.get_subject_averages(semester=semester, section=section)
    grade_dist = AnalyticsService.get_grade_distribution(semester=semester, subject_id=subject_id, section=section)
    pass_fail = AnalyticsService.get_pass_fail_stats(semester=semester, subject_id=subject_id, section=section)
    trends = AnalyticsService.get_test_performance_trends(semester=semester, subject_id=subject_id)
    all_subjects = SubjectService.get_all()

    return render_template(
        'faculty/analytics.html',
        summary=summary,
        subject_avg=subject_avg,
        grade_dist=grade_dist,
        pass_fail=pass_fail,
        trends=trends,
        subjects=all_subjects,
        selected_sem=semester,
        selected_subj=subject_id,
        selected_sec=section
    )

@faculty_bp.route('/alerts')
def alerts():
    semester = request.args.get('semester')
    subject_id = request.args.get('subject_id', type=int)
    risk_filter = request.args.get('risk_filter')

    all_alerts = AnomalyService.detect_anomalies(semester=semester, subject_id=subject_id, risk_filter=risk_filter)
    all_subjects = SubjectService.get_all()

    return render_template(
        'faculty/alerts.html',
        alerts=all_alerts,
        subjects=all_subjects,
        selected_sem=semester,
        selected_subj=subject_id,
        selected_risk=risk_filter
    )

@faculty_bp.route('/predictions')
def predictions():
    semester = request.args.get('semester')
    section = request.args.get('section')

    _, metadata = PredictionService.get_or_load_model()
    predictions_list = PredictionService.get_all_predictions(semester=semester, section=section)

    return render_template(
        'faculty/predictions.html',
        predictions=predictions_list,
        metadata=metadata,
        selected_sem=semester,
        selected_sec=section
    )

@faculty_bp.route('/reports')
def reports():
    all_students = Student.query.order_by(Student.roll_no.asc()).all()
    all_subjects = SubjectService.get_all()
    return render_template('faculty/reports.html', students=all_students, subjects=all_subjects)
