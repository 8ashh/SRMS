import io
import csv
from datetime import datetime
from fpdf import FPDF
from flask import current_app
from extensions import db
from models import Student, Subject, Mark, Attendance
from services.analytics_service import AnalyticsService
from services.anomaly_service import AnomalyService
from services.attendance_service import AttendanceService
from services.prediction_service import PredictionService

class MITSReportPDF(FPDF):
    """
    Custom PDF template styled for Madhav Institute of Technology & Science (MITS).
    Midnight Navy palette with headers, footers, page numbering and professional tables.
    """
    def __init__(self, title="Academic Report"):
        super().__init__(orientation='P', unit='mm', format='A4')
        self.report_title = title
        self.set_auto_page_break(auto=True, margin=15)

    def header(self):
        # Institution Header Bar
        self.set_fill_color(23, 37, 84)  # #172554 Primary Navy
        self.rect(0, 0, 210, 24, 'F')
        
        self.set_text_color(255, 255, 255)
        self.set_font('Helvetica', 'B', 12)
        self.set_xy(10, 4)
        self.cell(190, 6, "MADHAV INSTITUTE OF TECHNOLOGY & SCIENCE, GWALIOR", align='C', new_x='LMARGIN', new_y='NEXT')
        
        self.set_font('Helvetica', '', 8)
        self.cell(190, 4, "Academic Performance Analytics & Student Record Management System (SRMS)", align='C', new_x='LMARGIN', new_y='NEXT')
        
        # Sub-header bar
        self.set_fill_color(37, 99, 235)  # #2563EB
        self.rect(0, 24, 210, 1.5, 'F')
        
        # Report Title
        self.ln(6)
        self.set_text_color(23, 37, 84)
        self.set_font('Helvetica', 'B', 14)
        self.cell(120, 8, self.report_title, align='L')
        
        self.set_font('Helvetica', '', 8)
        self.set_text_color(100, 116, 139)
        gen_time = datetime.now().strftime('%d-%b-%Y %H:%M')
        self.cell(70, 8, f"Generated: {gen_time}", align='R', new_x='LMARGIN', new_y='NEXT')
        
        self.set_draw_color(226, 232, 240)
        self.set_line_width(0.4)
        self.line(10, 36, 200, 36)
        self.ln(4)

    def footer(self):
        self.set_y(-15)
        self.set_draw_color(226, 232, 240)
        self.line(10, self.get_y(), 200, self.get_y())
        self.ln(2)
        self.set_font('Helvetica', '', 8)
        self.set_text_color(100, 116, 139)
        self.cell(100, 5, "MITS Gwalior - Confidential Academic Document", align='L')
        self.cell(90, 5, f"Page {self.page_no()}/{{nb}}", align='R')


class ReportService:
    """
    Generates formal academic reports in CSV and PDF formats.
    """

    # ==========================
    # 1. STUDENT REPORT
    # ==========================
    @staticmethod
    def generate_student_csv(student_id):
        student = Student.query.get(student_id)
        if not student:
            return None

        marks = Mark.query.filter_by(student_id=student_id).all()
        att_info = AttendanceService.calculate_student_attendance(student_id)
        pred_info = PredictionService.predict_for_student(student_id)

        output = io.StringIO()
        writer = csv.writer(output)

        writer.writerow(["MITS GWALIOR - INDIVIDUAL STUDENT ACADEMIC DOSSIER"])
        writer.writerow(["Roll Number", student.roll_no])
        writer.writerow(["Student Name", student.name])
        writer.writerow(["Semester", student.semester])
        writer.writerow(["Section", student.section])
        writer.writerow(["Overall Attendance", f"{att_info['percentage']}% ({att_info['present']}/{att_info['total']})"])
        if pred_info and pred_info.get('status') == 'success':
            writer.writerow(["Predicted Final Score", f"{pred_info['predicted_score']}%"])
            writer.writerow(["Predicted Grade", pred_info['predicted_grade']])
        writer.writerow([])

        writer.writerow(["Subject Code", "Subject Name", "Test No", "Score", "Max Score", "Percentage (%)"])
        for m in marks:
            writer.writerow([
                m.subject.code,
                m.subject.name,
                f"Test {m.test_no}",
                m.score,
                m.max_score,
                m.percentage
            ])

        return output.getvalue().encode('utf-8')

    @staticmethod
    def generate_student_pdf(student_id):
        student = Student.query.get(student_id)
        if not student:
            return None

        marks = Mark.query.filter_by(student_id=student_id).order_by(Mark.subject_id.asc(), Mark.test_no.asc()).all()
        att_info = AttendanceService.calculate_student_attendance(student_id)
        pred_info = PredictionService.predict_for_student(student_id)
        alerts = AnomalyService.get_student_alerts(student_id)

        pdf = MITSReportPDF(title=f"Student Academic Dossier: {student.roll_no}")
        pdf.alias_nb_pages()
        pdf.add_page()

        # Student Details Box
        pdf.set_fill_color(239, 246, 255)  # Light blue #EFF6FF
        pdf.set_draw_color(191, 219, 254)
        pdf.rect(10, 39, 190, 24, 'DF')

        pdf.set_text_color(15, 23, 42)
        pdf.set_font('Helvetica', 'B', 10)
        pdf.set_xy(14, 42)
        pdf.cell(40, 5, "Student Name:")
        pdf.set_font('Helvetica', '', 10)
        pdf.cell(55, 5, student.name)

        pdf.set_font('Helvetica', 'B', 10)
        pdf.cell(40, 5, "Roll Number:")
        pdf.set_font('Helvetica', '', 10)
        pdf.cell(45, 5, student.roll_no)

        pdf.set_xy(14, 49)
        pdf.set_font('Helvetica', 'B', 10)
        pdf.cell(40, 5, "Class & Semester:")
        pdf.set_font('Helvetica', '', 10)
        pdf.cell(55, 5, f"Semester {student.semester} - Section {student.section}")

        pdf.set_font('Helvetica', 'B', 10)
        pdf.cell(40, 5, "Total Attendance:")
        pdf.set_font('Helvetica', '', 10)
        pdf.cell(45, 5, f"{att_info['percentage']}% ({att_info['present']}/{att_info['total']} Classes)")

        pdf.set_xy(14, 56)
        pdf.set_font('Helvetica', 'B', 10)
        pdf.cell(40, 5, "Predicted Outcome:")
        pdf.set_font('Helvetica', '', 10)
        if pred_info and pred_info.get('status') == 'success':
            pdf.cell(55, 5, f"Score: {pred_info['predicted_score']}% (Grade {pred_info['predicted_grade']})")
        else:
            pdf.cell(55, 5, "Prediction Pending")

        pdf.ln(14)

        # Marks Table Heading
        pdf.set_font('Helvetica', 'B', 11)
        pdf.set_text_color(23, 37, 84)
        pdf.cell(190, 6, "Academic Assessment Records", new_x='LMARGIN', new_y='NEXT')
        pdf.ln(1)

        # Table Header
        pdf.set_fill_color(23, 37, 84)
        pdf.set_text_color(255, 255, 255)
        pdf.set_font('Helvetica', 'B', 9)
        pdf.cell(30, 7, "Subject Code", 1, 0, 'C', fill=True)
        pdf.cell(75, 7, "Subject Name", 1, 0, 'L', fill=True)
        pdf.cell(25, 7, "Test", 1, 0, 'C', fill=True)
        pdf.cell(30, 7, "Score / Max", 1, 0, 'C', fill=True)
        pdf.cell(30, 7, "Percentage", 1, 1, 'C', fill=True)

        # Table Rows
        pdf.set_text_color(30, 41, 59)
        pdf.set_font('Helvetica', '', 8.5)
        fill = False

        if not marks:
            pdf.cell(190, 7, "No assessment records registered for this student.", 1, 1, 'C')
        else:
            for m in marks:
                pdf.set_fill_color(248, 250, 252) if fill else pdf.set_fill_color(255, 255, 255)
                pdf.cell(30, 6, m.subject.code, 1, 0, 'C', fill=fill)
                pdf.cell(75, 6, m.subject.name[:38], 1, 0, 'L', fill=fill)
                pdf.cell(25, 6, f"Test {m.test_no}", 1, 0, 'C', fill=fill)
                pdf.cell(30, 6, f"{m.score} / {m.max_score}", 1, 0, 'C', fill=fill)
                pdf.cell(30, 6, f"{m.percentage}%", 1, 1, 'C', fill=fill)
                fill = not fill

        # Risk Alerts & Anomaly Notices Section
        if alerts:
            pdf.ln(5)
            pdf.set_font('Helvetica', 'B', 11)
            pdf.set_text_color(220, 38, 38)
            pdf.cell(190, 6, "Academic Monitoring Notices & Alerts", new_x='LMARGIN', new_y='NEXT')
            pdf.ln(1)

            pdf.set_fill_color(254, 242, 242)
            pdf.set_text_color(185, 28, 28)
            pdf.set_font('Helvetica', 'B', 8.5)
            pdf.cell(35, 6, "Risk Classification", 1, 0, 'C', fill=True)
            pdf.cell(40, 6, "Course & Test", 1, 0, 'L', fill=True)
            pdf.cell(115, 6, "Monitoring Diagnostic Reason", 1, 1, 'L', fill=True)

            pdf.set_font('Helvetica', '', 8)
            pdf.set_text_color(51, 65, 85)
            for a in alerts:
                pdf.cell(35, 6, a['risk_level'], 1, 0, 'C')
                pdf.cell(40, 6, f"{a['subject_code']} (Test {a['test_no']})", 1, 0, 'L')
                pdf.cell(115, 6, a['reason'][:70], 1, 1, 'L')

        return bytes(pdf.output())


    # ==========================
    # 2. CLASS PERFORMANCE REPORT
    # ==========================
    @staticmethod
    def generate_class_performance_csv(semester=None, section=None):
        summary = AnalyticsService.get_overall_summary(semester=semester, section=section)
        subject_avg = AnalyticsService.get_subject_averages(semester=semester, section=section)
        grade_dist = AnalyticsService.get_grade_distribution(semester=semester, section=section)
        pass_fail = AnalyticsService.get_pass_fail_stats(semester=semester, section=section)

        output = io.StringIO()
        writer = csv.writer(output)

        writer.writerow(["MITS GWALIOR - CLASS ACADEMIC PERFORMANCE REPORT"])
        writer.writerow(["Semester Filter", semester if semester else "All Semesters"])
        writer.writerow(["Section Filter", section if section else "All Sections"])
        writer.writerow(["Total Students", summary['total_students']])
        writer.writerow(["Average Percentage", f"{summary['overall_avg_percentage']}%"])
        writer.writerow(["Overall Pass Rate", f"{summary['overall_pass_rate']}%"])
        writer.writerow(["Average Attendance", f"{summary['avg_attendance']}%"])
        writer.writerow([])

        writer.writerow(["SUBJECT-WISE PERFORMANCE OVERVIEW"])
        writer.writerow(["Subject Code", "Subject Name", "Average Score", "Average (%)", "Min (%)", "Max (%)", "Std Dev"])
        for s in subject_avg.get('table_data', []):
            writer.writerow([
                s['subject_code'], s['subject_name'], s['avg_score'],
                s['avg_percentage'], s['min_percentage'], s['max_percentage'], s['std_percentage']
            ])
        writer.writerow([])

        writer.writerow(["GRADE DISTRIBUTION"])
        for label, count in zip(grade_dist['labels'], grade_dist['counts']):
            writer.writerow([label, count])

        return output.getvalue().encode('utf-8')

    @staticmethod
    def generate_class_performance_pdf(semester=None, section=None):
        summary = AnalyticsService.get_overall_summary(semester=semester, section=section)
        subject_avg = AnalyticsService.get_subject_averages(semester=semester, section=section)
        grade_dist = AnalyticsService.get_grade_distribution(semester=semester, section=section)
        pass_fail = AnalyticsService.get_pass_fail_stats(semester=semester, section=section)

        cohort_title = f"Class Performance: Sem {semester}" if semester else "Institutional Academic Performance Report"
        if section:
            cohort_title += f" (Sec {section})"

        pdf = MITSReportPDF(title=cohort_title)
        pdf.alias_nb_pages()
        pdf.add_page()

        # KPI Summary Grid
        pdf.set_fill_color(248, 250, 252)
        pdf.set_draw_color(226, 232, 240)
        pdf.rect(10, 39, 190, 20, 'DF')

        pdf.set_font('Helvetica', 'B', 8.5)
        pdf.set_text_color(100, 116, 139)
        pdf.set_xy(14, 42)
        pdf.cell(45, 4, "TOTAL ENROLLED")
        pdf.cell(45, 4, "COHORT AVERAGE")
        pdf.cell(45, 4, "OVERALL PASS RATE")
        pdf.cell(45, 4, "AVERAGE ATTENDANCE")

        pdf.set_font('Helvetica', 'B', 12)
        pdf.set_text_color(23, 37, 84)
        pdf.set_xy(14, 48)
        pdf.cell(45, 7, str(summary['total_students']))
        pdf.cell(45, 7, f"{summary['overall_avg_percentage']}%")
        pdf.cell(45, 7, f"{summary['overall_pass_rate']}%")
        pdf.cell(45, 7, f"{summary['avg_attendance']}%")

        pdf.ln(15)

        # Subject-wise table
        pdf.set_font('Helvetica', 'B', 11)
        pdf.set_text_color(23, 37, 84)
        pdf.cell(190, 6, "Subject-wise Performance Breakdown", new_x='LMARGIN', new_y='NEXT')
        pdf.ln(1)

        pdf.set_fill_color(23, 37, 84)
        pdf.set_text_color(255, 255, 255)
        pdf.set_font('Helvetica', 'B', 8.5)
        pdf.cell(25, 7, "Code", 1, 0, 'C', fill=True)
        pdf.cell(70, 7, "Subject Name", 1, 0, 'L', fill=True)
        pdf.cell(25, 7, "Avg Score", 1, 0, 'C', fill=True)
        pdf.cell(25, 7, "Avg %", 1, 0, 'C', fill=True)
        pdf.cell(25, 7, "Min / Max", 1, 0, 'C', fill=True)
        pdf.cell(20, 7, "Std Dev", 1, 1, 'C', fill=True)

        pdf.set_text_color(30, 41, 59)
        pdf.set_font('Helvetica', '', 8)
        fill = False

        for row in subject_avg.get('table_data', []):
            pdf.set_fill_color(248, 250, 252) if fill else pdf.set_fill_color(255, 255, 255)
            pdf.cell(25, 6, row['subject_code'], 1, 0, 'C', fill=fill)
            pdf.cell(70, 6, row['subject_name'][:36], 1, 0, 'L', fill=fill)
            pdf.cell(25, 6, str(row['avg_score']), 1, 0, 'C', fill=fill)
            pdf.cell(25, 6, f"{row['avg_percentage']}%", 1, 0, 'C', fill=fill)
            pdf.cell(25, 6, f"{row['min_percentage']}% / {row['max_percentage']}%", 1, 0, 'C', fill=fill)
            pdf.cell(20, 6, str(row['std_percentage']), 1, 1, 'C', fill=fill)
            fill = not fill

        # Grade Distribution & Pass/Fail Tables Side-by-Side
        pdf.ln(6)
        pdf.set_font('Helvetica', 'B', 11)
        pdf.set_text_color(23, 37, 84)
        pdf.cell(92, 6, "Grade Distribution")
        pdf.cell(6, 6, "")
        pdf.cell(92, 6, "Pass / Fail Breakdown", new_x='LMARGIN', new_y='NEXT')
        pdf.ln(1)

        # Grade table
        pdf.set_fill_color(37, 99, 235)
        pdf.set_text_color(255, 255, 255)
        pdf.set_font('Helvetica', 'B', 8.5)
        pdf.cell(52, 6, "Grade Tier", 1, 0, 'L', fill=True)
        pdf.cell(20, 6, "Count", 1, 0, 'C', fill=True)
        pdf.cell(20, 6, "Share %", 1, 0, 'C', fill=True)

        pdf.cell(6, 6, "")  # spacer

        pdf.cell(52, 6, "Status Category", 1, 0, 'L', fill=True)
        pdf.cell(20, 6, "Count", 1, 0, 'C', fill=True)
        pdf.cell(20, 6, "Share %", 1, 1, 'C', fill=True)

        pdf.set_text_color(30, 41, 59)
        pdf.set_font('Helvetica', '', 8)

        grade_keys = ['A', 'B', 'C', 'F']
        grade_labels = ['Grade A (>=75%)', 'Grade B (60-74%)', 'Grade C (40-59%)', 'Grade F (<40%)']
        pf_rows = [
            ("Passed Assessments", pass_fail['passed'], f"{pass_fail['pass_rate']}%"),
            ("Failed Assessments", pass_fail['failed'], f"{pass_fail['fail_rate']}%"),
            ("Passing Criteria", ">= 40.0%", "Threshold"),
            ("Evaluation Status", "Verified", "Academic")
        ]

        for i in range(4):
            g_k = grade_keys[i]
            g_lbl = grade_labels[i]
            g_cnt = grade_dist['raw_counts'].get(g_k, 0)
            g_pct = grade_dist['percentages'].get(g_k, 0.0)

            pdf.cell(52, 5.5, g_lbl, 1, 0, 'L')
            pdf.cell(20, 5.5, str(g_cnt), 1, 0, 'C')
            pdf.cell(20, 5.5, f"{g_pct}%", 1, 0, 'C')

            pdf.cell(6, 5.5, "")  # spacer

            pf = pf_rows[i]
            pdf.cell(52, 5.5, pf[0], 1, 0, 'L')
            pdf.cell(20, 5.5, str(pf[1]), 1, 0, 'C')
            pdf.cell(20, 5.5, str(pf[2]), 1, 1, 'C')

        return bytes(pdf.output())


    # ==========================
    # 3. ACADEMIC RISK ALERTS REPORT
    # ==========================
    @staticmethod
    def generate_risk_alerts_csv(semester=None, subject_id=None, risk_filter=None):
        alerts = AnomalyService.detect_anomalies(semester=semester, subject_id=subject_id, risk_filter=risk_filter)

        output = io.StringIO()
        writer = csv.writer(output)

        writer.writerow(["MITS GWALIOR - EARLY ACADEMIC INTERVENTION & RISK REPORT"])
        writer.writerow(["Generated Date", datetime.now().strftime('%Y-%m-%d %H:%M:%S')])
        writer.writerow(["Total Identified Flags", len(alerts)])
        writer.writerow([])

        writer.writerow(["Roll No", "Student Name", "Semester", "Section", "Course", "Test", "Current Score", "Previous Score", "Z-Score", "Attendance", "Risk Level", "Alert Reason"])
        for a in alerts:
            writer.writerow([
                a['roll_no'], a['student_name'], a['semester'], a['section'],
                a['subject_code'], f"Test {a['test_no']}", a['current_score'],
                a['previous_score'], a['z_score'], a['attendance_pct'],
                a['risk_level'], a['reason']
            ])

        return output.getvalue().encode('utf-8')

    @staticmethod
    def generate_risk_alerts_pdf(semester=None, subject_id=None, risk_filter=None):
        alerts = AnomalyService.detect_anomalies(semester=semester, subject_id=subject_id, risk_filter=risk_filter)

        pdf = MITSReportPDF(title="Academic Early Warning & Intervention Report")
        pdf.alias_nb_pages()
        pdf.add_page()

        pdf.set_fill_color(254, 242, 242)
        pdf.set_draw_color(254, 202, 202)
        pdf.rect(10, 39, 190, 16, 'DF')

        pdf.set_font('Helvetica', 'B', 9)
        pdf.set_text_color(185, 28, 28)
        pdf.set_xy(14, 42)
        pdf.cell(180, 5, "EARLY INTERVENTION MANDATE", new_x='LMARGIN', new_y='NEXT')
        pdf.set_font('Helvetica', '', 8)
        pdf.set_text_color(127, 29, 29)
        pdf.set_xy(14, 47)
        pdf.cell(180, 5, f"Identified {len(alerts)} students requiring academic counseling prior to final semester examinations.")

        pdf.ln(12)

        # Table Header
        pdf.set_fill_color(23, 37, 84)
        pdf.set_text_color(255, 255, 255)
        pdf.set_font('Helvetica', 'B', 8)
        pdf.cell(20, 7, "Roll No", 1, 0, 'C', fill=True)
        pdf.cell(38, 7, "Student Name", 1, 0, 'L', fill=True)
        pdf.cell(22, 7, "Subject", 1, 0, 'C', fill=True)
        pdf.cell(18, 7, "Score", 1, 0, 'C', fill=True)
        pdf.cell(16, 7, "Z-Score", 1, 0, 'C', fill=True)
        pdf.cell(16, 7, "Attnd", 1, 0, 'C', fill=True)
        pdf.cell(22, 7, "Risk Tier", 1, 0, 'C', fill=True)
        pdf.cell(38, 7, "Diagnostic Reason", 1, 1, 'L', fill=True)

        pdf.set_text_color(30, 41, 59)
        pdf.set_font('Helvetica', '', 7.5)
        fill = False

        if not alerts:
            pdf.cell(190, 8, "No active academic anomaly flags detected in current cohort.", 1, 1, 'C')
        else:
            for a in alerts:
                pdf.set_fill_color(248, 250, 252) if fill else pdf.set_fill_color(255, 255, 255)
                pdf.cell(20, 6, a['roll_no'], 1, 0, 'C', fill=fill)
                pdf.cell(38, 6, a['student_name'][:20], 1, 0, 'L', fill=fill)
                pdf.cell(22, 6, f"{a['subject_code']} T{a['test_no']}", 1, 0, 'C', fill=fill)
                pdf.cell(18, 6, f"{a['current_percentage']}%", 1, 0, 'C', fill=fill)
                pdf.cell(16, 6, str(a['z_score']), 1, 0, 'C', fill=fill)
                pdf.cell(16, 6, a['attendance_pct'], 1, 0, 'C', fill=fill)
                pdf.cell(22, 6, a['risk_level'], 1, 0, 'C', fill=fill)
                pdf.cell(38, 6, a['reason'][:24] + "...", 1, 1, 'L', fill=fill)
                fill = not fill

        return bytes(pdf.output())
