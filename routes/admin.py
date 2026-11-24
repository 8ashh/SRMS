from datetime import datetime, date
from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from extensions import db
from models import Student, Subject, Mark, Attendance, User, AuditLog
from routes.auth import role_required
from services.student_service import StudentService
from services.subject_service import SubjectService
from services.marks_service import MarksService
from services.attendance_service import AttendanceService
from services.analytics_service import AnalyticsService
from services.anomaly_service import AnomalyService
from services.prediction_service import PredictionService
from services.audit_service import AuditService

admin_bp = Blueprint('admin', __name__, url_prefix='/admin')

# Apply role check to all admin routes
@admin_bp.before_request
@role_required(['admin'])
def before_request():
    pass


# ============================================================
# 1. DASHBOARD
# ============================================================
@admin_bp.route('/dashboard')
def dashboard():
    summary = AnalyticsService.get_overall_summary()
    faculty_count = User.query.filter_by(role='faculty').count()

    # Risk alerts count
    alerts = AnomalyService.detect_anomalies()
    high_risk_count = sum(1 for a in alerts if a['risk_level'] == 'High Risk')

    # Chart datasets
    grade_dist = AnalyticsService.get_grade_distribution()
    subject_avg = AnalyticsService.get_subject_averages()
    pass_fail = AnalyticsService.get_pass_fail_stats()
    trends = AnalyticsService.get_test_performance_trends()

    # Recent activities
    recent_students = Student.query.order_by(Student.created_at.desc()).limit(5).all()
    recent_marks = Mark.query.order_by(Mark.created_at.desc()).limit(5).all()
    recent_logs = AuditLog.query.order_by(AuditLog.timestamp.desc()).limit(6).all()

    return render_template(
        'admin/dashboard.html',
        summary=summary,
        faculty_count=faculty_count,
        total_risk_count=len(alerts),
        high_risk_count=high_risk_count,
        grade_dist=grade_dist,
        subject_avg=subject_avg,
        pass_fail=pass_fail,
        trends=trends,
        recent_students=recent_students,
        recent_marks=recent_marks,
        recent_logs=recent_logs,
        top_alerts=alerts[:5]
    )


# ============================================================
# 2. STUDENT MANAGEMENT
# ============================================================
@admin_bp.route('/students')
def students():
    search = request.args.get('search', '').strip()
    semester = request.args.get('semester', '').strip()
    section = request.args.get('section', '').strip()
    page = request.args.get('page', 1, type=int)

    pagination = StudentService.get_all(search=search, semester=semester, section=section, page=page, per_page=15)
    return render_template(
        'admin/students.html',
        pagination=pagination,
        search=search,
        semester=semester,
        section=section
    )


@admin_bp.route('/students/add', methods=['GET', 'POST'])
def add_student():
    if request.method == 'POST':
        roll_no = request.form.get('roll_no')
        name = request.form.get('name')
        semester = request.form.get('semester')
        section = request.form.get('section')

        student, err = StudentService.create_student(roll_no, name, semester, section)
        if err:
            flash(err, 'danger')
            return render_template('admin/student_form.html', student=None, roll_no=roll_no, name=name, semester=semester, section=section)

        flash(f"Student '{student.name}' ({student.roll_no}) added successfully.", 'success')
        return redirect(url_for('admin.students'))

    return render_template('admin/student_form.html', student=None)


@admin_bp.route('/students/<int:student_id>')
def student_profile(student_id):
    student = StudentService.get_by_id(student_id)
    if not student:
        flash("Student record not found.", "danger")
        return redirect(url_for('admin.students'))

    marks = MarksService.get_student_marks(student_id)
    att_info = AttendanceService.calculate_student_attendance(student_id)
    alerts = AnomalyService.get_student_alerts(student_id)
    prediction = PredictionService.predict_for_student(student_id)
    analytics = AnalyticsService.get_individual_student_analytics(student_id)

    return render_template(
        'admin/student_profile.html',
        student=student,
        marks=marks,
        att_info=att_info,
        alerts=alerts,
        prediction=prediction,
        analytics=analytics
    )


@admin_bp.route('/students/edit/<int:student_id>', methods=['GET', 'POST'])
def edit_student(student_id):
    student = StudentService.get_by_id(student_id)
    if not student:
        flash("Student record not found.", "danger")
        return redirect(url_for('admin.students'))

    if request.method == 'POST':
        roll_no = request.form.get('roll_no')
        name = request.form.get('name')
        semester = request.form.get('semester')
        section = request.form.get('section')

        updated, err = StudentService.update_student(student_id, roll_no, name, semester, section)
        if err:
            flash(err, 'danger')
            return render_template('admin/student_form.html', student=student)

        flash(f"Student '{updated.name}' updated successfully.", 'success')
        return redirect(url_for('admin.students'))

    return render_template('admin/student_form.html', student=student)


@admin_bp.route('/students/delete/<int:student_id>', methods=['POST'])
def delete_student(student_id):
    success, err = StudentService.delete_student(student_id)
    if success:
        flash("Student and associated academic records removed.", "success")
    else:
        flash(err, "danger")
    return redirect(url_for('admin.students'))


# ============================================================
# 3. FACULTY MANAGEMENT
# ============================================================
@admin_bp.route('/faculty', methods=['GET', 'POST'])
def faculty():
    if request.method == 'POST':
        username = request.form.get('username', '').strip().lower()
        password = request.form.get('password', '').strip()
        faculty_name = request.form.get('faculty_name', '').strip()

        if not username or not password or not faculty_name:
            flash("All faculty account fields are required.", "danger")
            return redirect(url_for('admin.faculty'))

        if User.query.filter_by(username=username).first():
            flash(f"Username '{username}' is already in use.", "danger")
            return redirect(url_for('admin.faculty'))

        new_faculty = User(
            username=username,
            role='faculty',
            faculty_name=faculty_name
        )
        new_faculty.set_password(password)
        db.session.add(new_faculty)
        db.session.commit()

        AuditService.log(
            action="ADD_FACULTY",
            module="Faculty",
            record_id=new_faculty.user_id,
            description=f"Created faculty account for '{faculty_name}' (username: {username})."
        )
        flash(f"Faculty account for '{faculty_name}' created successfully.", "success")
        return redirect(url_for('admin.faculty'))

    faculty_list = User.query.filter_by(role='faculty').order_by(User.faculty_name.asc()).all()
    return render_template('admin/faculty.html', faculty_list=faculty_list)


@admin_bp.route('/faculty/delete/<int:user_id>', methods=['POST'])
def delete_faculty(user_id):
    user = User.query.get(user_id)
    if user and user.role == 'faculty':
        name = user.faculty_name or user.username
        db.session.delete(user)
        db.session.commit()
        AuditService.log(
            action="DELETE_FACULTY",
            module="Faculty",
            record_id=user_id,
            description=f"Removed faculty account '{name}'."
        )
        flash(f"Faculty account '{name}' deleted.", "success")
    else:
        flash("Faculty account not found.", "danger")
    return redirect(url_for('admin.faculty'))


# ============================================================
# 4. SUBJECT MANAGEMENT
# ============================================================
@admin_bp.route('/subjects', methods=['GET', 'POST'])
def subjects():
    if request.method == 'POST':
        code = request.form.get('code')
        name = request.form.get('name')

        subj, err = SubjectService.create_subject(code, name)
        if err:
            flash(err, "danger")
        else:
            flash(f"Subject '{subj.name}' ({subj.code}) created.", "success")
        return redirect(url_for('admin.subjects'))

    subjects_list = SubjectService.get_all()
    return render_template('admin/subjects.html', subjects=subjects_list)


@admin_bp.route('/subjects/edit/<int:subject_id>', methods=['POST'])
def edit_subject(subject_id):
    code = request.form.get('code')
    name = request.form.get('name')
    updated, err = SubjectService.update_subject(subject_id, code, name)
    if err:
        flash(err, "danger")
    else:
        flash(f"Subject updated to '{updated.name}' ({updated.code}).", "success")
    return redirect(url_for('admin.subjects'))


@admin_bp.route('/subjects/delete/<int:subject_id>', methods=['POST'])
def delete_subject(subject_id):
    success, err = SubjectService.delete_subject(subject_id)
    if success:
        flash("Subject and associated marks/attendance deleted.", "success")
    else:
        flash(err, "danger")
    return redirect(url_for('admin.subjects'))


# ============================================================
# 5. MARKS MANAGEMENT
# ============================================================
@admin_bp.route('/marks', methods=['GET', 'POST'])
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
            flash(f"Recorded Test {mark.test_no} score ({mark.score}/{mark.max_score}, {mark.percentage}%) successfully.", "success")
        return redirect(url_for('admin.marks'))

    student_id = request.args.get('student_id', type=int)
    subject_id = request.args.get('subject_id', type=int)
    semester = request.args.get('semester')
    test_no = request.args.get('test_no', type=int)
    page = request.args.get('page', 1, type=int)

    pagination = MarksService.get_all(student_id=student_id, subject_id=subject_id, semester=semester, test_no=test_no, page=page, per_page=20)
    all_students = Student.query.order_by(Student.roll_no.asc()).all()
    all_subjects = SubjectService.get_all()

    return render_template(
        'admin/marks.html',
        pagination=pagination,
        students=all_students,
        subjects=all_subjects,
        selected_student=student_id,
        selected_subject=subject_id,
        selected_sem=semester,
        selected_test=test_no
    )


@admin_bp.route('/marks/edit/<int:mark_id>', methods=['POST'])
def edit_mark(mark_id):
    score = request.form.get('score')
    max_score = request.form.get('max_score')
    test_no = request.form.get('test_no')

    updated, err = MarksService.update_mark(mark_id, score, max_score, test_no)
    if err:
        flash(err, "danger")
    else:
        flash(f"Updated score to {updated.score}/{updated.max_score} ({updated.percentage}%).", "success")
    return redirect(request.referrer or url_for('admin.marks'))


@admin_bp.route('/marks/delete/<int:mark_id>', methods=['POST'])
def delete_mark(mark_id):
    success, err = MarksService.delete_mark(mark_id)
    if success:
        flash("Mark record removed.", "success")
    else:
        flash(err, "danger")
    return redirect(request.referrer or url_for('admin.marks'))


# ============================================================
# 6. ATTENDANCE MANAGEMENT
# ============================================================
@admin_bp.route('/attendance', methods=['GET', 'POST'])
def attendance():
    if request.method == 'POST':
        # Batch attendance recording
        subject_id = request.form.get('subject_id', type=int)
        att_date = request.form.get('date')

        # Read student attendance radio buttons: status_<student_id>
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
        return redirect(url_for('admin.attendance', subject_id=subject_id, date=att_date))

    subject_id = request.args.get('subject_id', type=int)
    att_date = request.args.get('date', date.today().strftime('%Y-%m-%d'))
    student_id = request.args.get('student_id', type=int)
    page = request.args.get('page', 1, type=int)

    all_subjects = SubjectService.get_all()
    all_students = Student.query.order_by(Student.roll_no.asc()).all()

    # For batch form: if subject_id is selected, load existing attendance for that date
    current_statuses = {}
    if subject_id and att_date:
        records = Attendance.query.filter_by(subject_id=subject_id, date=datetime.strptime(att_date, '%Y-%m-%d').date()).all()
        for r in records:
            current_statuses[r.student_id] = r.status

    pagination = AttendanceService.get_all(student_id=student_id, subject_id=subject_id, att_date=att_date if not student_id else None, page=page, per_page=20)

    return render_template(
        'admin/attendance.html',
        subjects=all_subjects,
        students=all_students,
        selected_subject=subject_id,
        selected_date=att_date,
        selected_student=student_id,
        current_statuses=current_statuses,
        pagination=pagination,
        today_date=date.today().strftime('%Y-%m-%d')
    )


# ============================================================
# 7. ANALYTICS, ALERTS, PREDICTIONS, AUDIT, REPORTS
# ============================================================
@admin_bp.route('/analytics')
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
        'admin/analytics.html',
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


@admin_bp.route('/alerts')
def alerts():
    semester = request.args.get('semester')
    subject_id = request.args.get('subject_id', type=int)
    risk_filter = request.args.get('risk_filter')

    all_alerts = AnomalyService.detect_anomalies(semester=semester, subject_id=subject_id, risk_filter=risk_filter)
    all_subjects = SubjectService.get_all()

    return render_template(
        'admin/alerts.html',
        alerts=all_alerts,
        subjects=all_subjects,
        selected_sem=semester,
        selected_subj=subject_id,
        selected_risk=risk_filter
    )


@admin_bp.route('/predictions', methods=['GET', 'POST'])
def predictions():
    if request.method == 'POST':
        model_type = request.form.get('model_type', 'linear')
        force_demo = request.form.get('force_demo') == '1'
        metadata = PredictionService.train_model(force_demo=force_demo, model_type=model_type)
        flash(f"Trained {metadata['model_name']} model (MAE: {metadata['mae']}, R²: {metadata['r2_score']}).", "success")
        return redirect(url_for('admin.predictions'))

    semester = request.args.get('semester')
    section = request.args.get('section')

    _, metadata = PredictionService.get_or_load_model()
    predictions_list = PredictionService.get_all_predictions(semester=semester, section=section)

    return render_template(
        'admin/predictions.html',
        predictions=predictions_list,
        metadata=metadata,
        selected_sem=semester,
        selected_sec=section
    )


@admin_bp.route('/reports')
def reports():
    all_students = Student.query.order_by(Student.roll_no.asc()).all()
    all_subjects = SubjectService.get_all()
    return render_template('admin/reports.html', students=all_students, subjects=all_subjects)


@admin_bp.route('/audit-logs')
def audit_logs():
    module = request.args.get('module')
    action = request.args.get('action')
    page = request.args.get('page', 1, type=int)

    query = AuditLog.query
    if module:
        query = query.filter(AuditLog.module == module)
    if action:
        query = query.filter(AuditLog.action == action)

    pagination = query.order_by(AuditLog.timestamp.desc()).paginate(page=page, per_page=25, error_out=False)
    return render_template('admin/audit_logs.html', pagination=pagination, selected_module=module, selected_action=action)
