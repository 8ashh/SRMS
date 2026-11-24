import pandas as pd
import numpy as np
from datetime import datetime
from flask import current_app
from extensions import db
from models import Mark, Student, Subject, Attendance
from services.attendance_service import AttendanceService

class AnomalyService:
    """
    Statistical Anomaly Detection Service.
    Implements:
      1. Z-score Anomaly Detection (Cohort comparison for same subject & test)
      2. Falling Performance Trend Detection (>= 15% decline across sequential tests)
      3. Risk Classification (High, Medium, Low)
    """

    @staticmethod
    def detect_anomalies(semester=None, subject_id=None, risk_filter=None):
        """
        Scans student marks and attendance records to generate academic risk alerts.
        Returns deduplicated alerts categorized by risk severity.
        """
        alerts = []
        z_thresh = current_app.config.get('Z_SCORE_THRESHOLD', -1.5) if current_app else -1.5
        drop_thresh = current_app.config.get('PERFORMANCE_DROP_THRESHOLD', 15.0) if current_app else 15.0
        critical_att = current_app.config.get('ATTENDANCE_CRITICAL_THRESHOLD', 60.0) if current_app else 60.0

        # Load all marks
        query = db.session.query(
            Mark.mark_id,
            Mark.student_id,
            Student.roll_no,
            Student.name.label('student_name'),
            Student.semester,
            Student.section,
            Mark.subject_id,
            Subject.code.label('subject_code'),
            Subject.name.label('subject_name'),
            Mark.test_no,
            Mark.score,
            Mark.max_score,
            Mark.created_at
        ).join(Student, Mark.student_id == Student.student_id)\
         .join(Subject, Mark.subject_id == Subject.subject_id)

        if semester:
            query = query.filter(Student.semester == int(semester))
        if subject_id:
            query = query.filter(Mark.subject_id == int(subject_id))

        results = query.all()
        if not results:
            return []

        df = pd.DataFrame([r._asdict() for r in results])
        df['percentage'] = np.round((df['score'] / df['max_score']) * 100.0, 2)

        # 1. Method A: Z-score calculation per (subject_id, test_no) group
        z_scores_map = {}
        grouped = df.groupby(['subject_id', 'test_no'])

        for (subj, t_no), group in grouped:
            # Need at least 3 students to compute meaningful standard deviation
            if len(group) >= 3:
                mean_val = float(group['percentage'].mean())
                std_val = float(group['percentage'].std())
                if std_val > 0.001:
                    for _, row in group.iterrows():
                        z = (row['percentage'] - mean_val) / std_val
                        z_scores_map[row['mark_id']] = (round(z, 2), round(mean_val, 2), round(std_val, 2))

        # 2. Method B: Sequential Test Performance Drop per student & subject
        df_sorted = df.sort_values(by=['student_id', 'subject_id', 'test_no'])
        
        # Track generated alerts to avoid duplicates
        seen_keys = set()

        for (s_id, sub_id), s_sub_group in df_sorted.groupby(['student_id', 'subject_id']):
            test_records = s_sub_group.to_dict(orient='records')
            
            # Fetch student attendance
            att_info = AttendanceService.calculate_student_attendance(s_id, sub_id)
            att_pct = att_info['percentage']

            for i in range(len(test_records)):
                current = test_records[i]
                mark_id = current['mark_id']
                current_pct = current['percentage']
                z_info = z_scores_map.get(mark_id)
                z_val = z_info[0] if z_info else None
                class_mean = z_info[1] if z_info else None

                prev_pct = None
                pct_drop = 0.0
                if i > 0:
                    prev = test_records[i - 1]
                    prev_pct = prev['percentage']
                    pct_drop = round(prev_pct - current_pct, 2)

                # Detection criteria
                is_z_anomaly = (z_val is not None) and (z_val <= z_thresh)
                is_falling_trend = (prev_pct is not None) and (pct_drop >= drop_thresh)
                is_low_attendance = (att_info['total'] >= 3) and (att_pct < critical_att)

                if is_z_anomaly or is_falling_trend or is_low_attendance:
                    # Risk Classification Logic
                    reasons = []
                    severity_points = 0

                    if is_z_anomaly:
                        reasons.append(f"Performance Z-score of {z_val} is below threshold ({z_thresh}) against class average ({class_mean}%).")
                        severity_points += 2 if z_val <= -2.0 else 1

                    if is_falling_trend:
                        reasons.append(f"Significant performance decline: Score dropped by {pct_drop}% (from Test {test_records[i-1]['test_no']} at {prev_pct}% to Test {current['test_no']} at {current_pct}%).")
                        severity_points += 2

                    if is_low_attendance:
                        reasons.append(f"Low subject attendance: Currently at {att_pct}% (below minimum {critical_att}% threshold).")
                        severity_points += 1

                    if severity_points >= 3 or (is_z_anomaly and is_falling_trend):
                        risk_level = 'High Risk'
                        badge_color = 'danger'
                    elif severity_points >= 1:
                        risk_level = 'Medium Risk'
                        badge_color = 'warning'
                    else:
                        risk_level = 'Low Risk'
                        badge_color = 'info'

                    # Create alert object
                    alert_key = (s_id, sub_id, current['test_no'])
                    if alert_key not in seen_keys:
                        seen_keys.add(alert_key)
                        alerts.append({
                            'student_id': s_id,
                            'student_name': current['student_name'],
                            'roll_no': current['roll_no'],
                            'semester': current['semester'],
                            'section': current['section'],
                            'subject_id': sub_id,
                            'subject_code': current['subject_code'],
                            'subject_name': current['subject_name'],
                            'test_no': current['test_no'],
                            'current_score': f"{current['score']}/{current['max_score']} ({current_pct}%)",
                            'current_percentage': current_pct,
                            'previous_score': f"{prev_pct}% (Test {test_records[i-1]['test_no']})" if prev_pct is not None else "N/A",
                            'z_score': z_val if z_val is not None else "N/A",
                            'class_mean': f"{class_mean}%" if class_mean is not None else "N/A",
                            'attendance_pct': f"{att_pct}%",
                            'risk_level': risk_level,
                            'badge_color': badge_color,
                            'reason': " | ".join(reasons),
                            'date_generated': current['created_at'].strftime('%Y-%m-%d') if current['created_at'] else datetime.utcnow().strftime('%Y-%m-%d')
                        })

        # Apply risk filter if requested
        if risk_filter:
            alerts = [a for a in alerts if a['risk_level'].lower() == risk_filter.lower()]

        # Sort with High Risk first
        priority_order = {'High Risk': 0, 'Medium Risk': 1, 'Low Risk': 2}
        alerts.sort(key=lambda x: (priority_order.get(x['risk_level'], 3), x['student_name']))

        return alerts

    @staticmethod
    def get_student_alerts(student_id):
        """Retrieve risk alerts specific to a single student (data isolation)."""
        all_alerts = AnomalyService.detect_anomalies()
        return [a for a in all_alerts if a['student_id'] == student_id]
