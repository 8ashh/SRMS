from flask import Blueprint, request, Response, session, flash, redirect, url_for
from routes.auth import login_required, role_required
from services.report_service import ReportService
from services.audit_service import AuditService

reports_bp = Blueprint('reports', __name__, url_prefix='/reports')

@reports_bp.route('/student/<int:student_id>/pdf')
@login_required
def student_pdf(student_id):
    # Role-based check: student can only download their own
    role = session.get('role')
    user_student_id = session.get('student_id')
    if role == 'student' and user_student_id != student_id:
        flash("Unauthorized to download records for another student.", "danger")
        return redirect(url_for('student.dashboard'))

    pdf_bytes = ReportService.generate_student_pdf(student_id)
    if not pdf_bytes:
        flash("Student record not found.", "danger")
        return redirect(request.referrer or url_for('auth.index'))

    AuditService.log(
        action="EXPORT_PDF",
        module="Reports",
        record_id=student_id,
        description=f"Generated Student PDF report for student ID {student_id}."
    )

    return Response(
        pdf_bytes,
        mimetype='application/pdf',
        headers={'Content-Disposition': f'attachment; filename=student_report_{student_id}.pdf'}
    )


@reports_bp.route('/student/<int:student_id>/csv')
@login_required
def student_csv(student_id):
    role = session.get('role')
    user_student_id = session.get('student_id')
    if role == 'student' and user_student_id != student_id:
        flash("Unauthorized to download records for another student.", "danger")
        return redirect(url_for('student.dashboard'))

    csv_data = ReportService.generate_student_csv(student_id)
    if not csv_data:
        flash("Student record not found.", "danger")
        return redirect(request.referrer or url_for('auth.index'))

    return Response(
        csv_data,
        mimetype='text/csv',
        headers={'Content-Disposition': f'attachment; filename=student_dossier_{student_id}.csv'}
    )


@reports_bp.route('/class/pdf')
@role_required(['admin', 'faculty'])
def class_pdf():
    semester = request.args.get('semester')
    section = request.args.get('section')
    pdf_bytes = ReportService.generate_class_performance_pdf(semester=semester, section=section)

    AuditService.log(
        action="EXPORT_PDF",
        module="Reports",
        description=f"Generated Class Performance PDF report (Sem: {semester}, Sec: {section})."
    )

    return Response(
        pdf_bytes,
        mimetype='application/pdf',
        headers={'Content-Disposition': 'attachment; filename=class_performance_report.pdf'}
    )


@reports_bp.route('/class/csv')
@role_required(['admin', 'faculty'])
def class_csv():
    semester = request.args.get('semester')
    section = request.args.get('section')
    csv_data = ReportService.generate_class_performance_csv(semester=semester, section=section)

    return Response(
        csv_data,
        mimetype='text/csv',
        headers={'Content-Disposition': 'attachment; filename=class_performance_report.csv'}
    )


@reports_bp.route('/risk/pdf')
@role_required(['admin', 'faculty'])
def risk_pdf():
    semester = request.args.get('semester')
    subject_id = request.args.get('subject_id')
    risk_filter = request.args.get('risk_filter')
    pdf_bytes = ReportService.generate_risk_alerts_pdf(semester=semester, subject_id=subject_id, risk_filter=risk_filter)

    AuditService.log(
        action="EXPORT_PDF",
        module="Reports",
        description="Generated Academic Early Warning & Risk PDF report."
    )

    return Response(
        pdf_bytes,
        mimetype='application/pdf',
        headers={'Content-Disposition': 'attachment; filename=academic_risk_report.pdf'}
    )


@reports_bp.route('/risk/csv')
@role_required(['admin', 'faculty'])
def risk_csv():
    semester = request.args.get('semester')
    subject_id = request.args.get('subject_id')
    risk_filter = request.args.get('risk_filter')
    csv_data = ReportService.generate_risk_alerts_csv(semester=semester, subject_id=subject_id, risk_filter=risk_filter)

    return Response(
        csv_data,
        mimetype='text/csv',
        headers={'Content-Disposition': 'attachment; filename=academic_risk_report.csv'}
    )
