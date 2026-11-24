import pandas as pd
import numpy as np
from flask import current_app
from extensions import db
from models import Mark, Student, Subject, Attendance

class AnalyticsService:
    """
    Academic Analytics Engine leveraging Pandas and NumPy.
    All calculations operate on actual database records.
    """

    @staticmethod
    def get_marks_dataframe(semester=None, subject_id=None, section=None):
        """Helper to load marks joined with student and subject data into a Pandas DataFrame."""
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
            Mark.max_score
        ).join(Student, Mark.student_id == Student.student_id)\
         .join(Subject, Mark.subject_id == Subject.subject_id)

        if semester:
            query = query.filter(Student.semester == int(semester))
        if subject_id:
            query = query.filter(Mark.subject_id == int(subject_id))
        if section:
            query = query.filter(Student.section == section)

        results = query.all()
        if not results:
            return pd.DataFrame()

        df = pd.DataFrame([r._asdict() for r in results])
        # Calculate percentage using numpy/pandas
        df['percentage'] = np.round((df['score'] / df['max_score']) * 100.0, 2)
        return df

    @staticmethod
    def get_overall_summary(semester=None, section=None):
        """Computes high-level KPI metrics across the institution or filtered cohort."""
        total_students = Student.query
        if semester:
            total_students = total_students.filter(Student.semester == int(semester))
        if section:
            total_students = total_students.filter(Student.section == section)
        student_count = total_students.count()

        subject_count = Subject.query.count()
        marks_count = Mark.query.count()

        # Overall average percentage
        df = AnalyticsService.get_marks_dataframe(semester=semester, section=section)
        overall_avg_percentage = float(np.round(df['percentage'].mean(), 2)) if not df.empty else 0.0

        # Pass/fail
        pass_thresh = current_app.config.get('PASSING_PERCENTAGE', 40.0) if current_app else 40.0
        passing_records = int((df['percentage'] >= pass_thresh).sum()) if not df.empty else 0
        failing_records = len(df) - passing_records if not df.empty else 0
        overall_pass_rate = float(np.round((passing_records / len(df)) * 100.0, 2)) if not df.empty else 0.0

        # Average attendance across all records
        att_query = Attendance.query
        total_att = att_query.count()
        present_att = att_query.filter(Attendance.status == 'Present').count()
        avg_attendance = float(np.round((present_att / total_att) * 100.0, 2)) if total_att > 0 else 0.0

        return {
            'total_students': student_count,
            'total_subjects': subject_count,
            'total_marks_records': marks_count,
            'overall_avg_percentage': overall_avg_percentage,
            'overall_pass_rate': overall_pass_rate,
            'passing_records': passing_records,
            'failing_records': failing_records,
            'avg_attendance': avg_attendance
        }

    @staticmethod
    def get_subject_averages(semester=None, section=None):
        """
        Calculates average score and percentage for each subject.
        Returns data formatted for Chart.js bar charts and data tables.
        """
        df = AnalyticsService.get_marks_dataframe(semester=semester, section=section)
        if df.empty:
            return {'labels': [], 'averages': [], 'table_data': []}

        # Group by subject code and name
        grouped = df.groupby(['subject_code', 'subject_name']).agg(
            avg_score=('score', 'mean'),
            avg_percentage=('percentage', 'mean'),
            record_count=('mark_id', 'count'),
            min_percentage=('percentage', 'min'),
            max_percentage=('percentage', 'max'),
            std_percentage=('percentage', 'std')
        ).reset_index()

        grouped['avg_percentage'] = grouped['avg_percentage'].round(2)
        grouped['avg_score'] = grouped['avg_score'].round(2)
        grouped['std_percentage'] = grouped['std_percentage'].fillna(0.0).round(2)

        labels = grouped['subject_code'].tolist()
        averages = grouped['avg_percentage'].tolist()
        table_data = grouped.to_dict(orient='records')

        return {
            'labels': labels,
            'averages': averages,
            'table_data': table_data
        }

    @staticmethod
    def get_grade_distribution(semester=None, subject_id=None, section=None):
        """
        Categorizes student marks into Grade A, B, C, F based on configurable cutoffs.
        Returns distribution counts and percentages.
        """
        df = AnalyticsService.get_marks_dataframe(semester=semester, subject_id=subject_id, section=section)
        grade_cutoffs = current_app.config.get('GRADE_CUTOFFS', {
            'A': 75.0, 'B': 60.0, 'C': 40.0, 'F': 0.0
        }) if current_app else {'A': 75.0, 'B': 60.0, 'C': 40.0, 'F': 0.0}

        counts = {'A': 0, 'B': 0, 'C': 0, 'F': 0}

        if not df.empty:
            def assign_grade(pct):
                if pct >= grade_cutoffs['A']:
                    return 'A'
                elif pct >= grade_cutoffs['B']:
                    return 'B'
                elif pct >= grade_cutoffs['C']:
                    return 'C'
                else:
                    return 'F'

            grades = df['percentage'].apply(assign_grade)
            value_counts = grades.value_counts().to_dict()
            for g in counts:
                counts[g] = int(value_counts.get(g, 0))

        total = sum(counts.values())
        percentages = {g: round((counts[g] / total * 100), 2) if total > 0 else 0.0 for g in counts}

        return {
            'labels': ['Grade A (>=75%)', 'Grade B (60-74%)', 'Grade C (40-59%)', 'Grade F (<40%)'],
            'counts': [counts['A'], counts['B'], counts['C'], counts['F']],
            'percentages': percentages,
            'raw_counts': counts,
            'total': total
        }

    @staticmethod
    def get_pass_fail_stats(semester=None, subject_id=None, section=None):
        """Computes overall and subject-wise pass/fail numbers and rates."""
        df = AnalyticsService.get_marks_dataframe(semester=semester, subject_id=subject_id, section=section)
        pass_thresh = current_app.config.get('PASSING_PERCENTAGE', 40.0) if current_app else 40.0

        if df.empty:
            return {
                'passed': 0, 'failed': 0, 'pass_rate': 0.0, 'fail_rate': 0.0, 'subject_breakdown': []
            }

        df['passed'] = df['percentage'] >= pass_thresh
        total = len(df)
        passed = int(df['passed'].sum())
        failed = total - passed

        pass_rate = round((passed / total * 100), 2) if total > 0 else 0.0
        fail_rate = round((failed / total * 100), 2) if total > 0 else 0.0

        # Subject-wise breakdown
        subj_summary = df.groupby(['subject_code', 'subject_name']).agg(
            total=('mark_id', 'count'),
            passed=('passed', 'sum')
        ).reset_index()
        subj_summary['passed'] = subj_summary['passed'].astype(int)
        subj_summary['failed'] = subj_summary['total'] - subj_summary['passed']
        subj_summary['pass_rate'] = ((subj_summary['passed'] / subj_summary['total']) * 100).round(2)
        subj_summary['fail_rate'] = (100.0 - subj_summary['pass_rate']).round(2)

        return {
            'passed': passed,
            'failed': failed,
            'pass_rate': pass_rate,
            'fail_rate': fail_rate,
            'subject_breakdown': subj_summary.to_dict(orient='records')
        }

    @staticmethod
    def get_test_performance_trends(semester=None, subject_id=None):
        """
        Computes performance trends across Test 1, Test 2, Test 3, etc.
        Returns line chart data of average scores across sequential tests.
        """
        df = AnalyticsService.get_marks_dataframe(semester=semester, subject_id=subject_id)
        if df.empty:
            return {'labels': [], 'datasets': []}

        # Check unique tests
        tests = sorted(df['test_no'].unique())
        test_labels = [f"Test {t}" for t in tests]

        # Overall class trend
        overall_trend = df.groupby('test_no')['percentage'].mean().round(2)
        datasets = [{
            'label': 'Cohort Average',
            'data': [float(overall_trend.get(t, 0.0)) for t in tests],
            'borderColor': '#2563EB',
            'backgroundColor': 'rgba(37, 99, 235, 0.1)',
            'fill': True,
            'tension': 0.3
        }]

        # If subject_id is not specified, include top subject lines
        if not subject_id:
            top_subjects = df['subject_code'].unique()[:4]
            colors = ['#10B981', '#F59E0B', '#EF4444', '#8B5CF6']
            for idx, code in enumerate(top_subjects):
                sub_df = df[df['subject_code'] == code]
                sub_trend = sub_df.groupby('test_no')['percentage'].mean().round(2)
                datasets.append({
                    'label': code,
                    'data': [float(sub_trend.get(t, 0.0)) for t in tests],
                    'borderColor': colors[idx % len(colors)],
                    'backgroundColor': 'transparent',
                    'borderDash': [5, 5],
                    'tension': 0.2
                })

        return {
            'labels': test_labels,
            'datasets': datasets
        }

    @staticmethod
    def get_individual_student_analytics(student_id):
        """
        Detailed performance analytics for a single student.
        Calculates subject-wise marks, attendance stats, and test trends.
        """
        student = Student.query.get(student_id)
        if not student:
            return None

        marks = Mark.query.filter_by(student_id=student_id).all()
        if not marks:
            return {
                'student': student,
                'avg_percentage': 0.0,
                'total_tests_taken': 0,
                'subject_performance': [],
                'test_trend': {'labels': [], 'scores': []},
                'passed_all': True
            }

        marks_data = [{
            'subject_code': m.subject.code,
            'subject_name': m.subject.name,
            'test_no': m.test_no,
            'score': m.score,
            'max_score': m.max_score,
            'percentage': m.percentage
        } for m in marks]

        df = pd.DataFrame(marks_data)
        avg_percentage = float(round(df['percentage'].mean(), 2))
        total_tests = len(df)

        pass_thresh = current_app.config.get('PASSING_PERCENTAGE', 40.0) if current_app else 40.0
        passed_all = bool((df['percentage'] >= pass_thresh).all())

        # Subject-wise aggregate
        subj_agg = df.groupby(['subject_code', 'subject_name']).agg(
            avg_pct=('percentage', 'mean'),
            tests_count=('test_no', 'count'),
            latest_pct=('percentage', 'last')
        ).reset_index()
        subj_agg['avg_pct'] = subj_agg['avg_pct'].round(2)

        # Sequential test trend for the student
        test_agg = df.groupby('test_no')['percentage'].mean().round(2)
        test_labels = [f"Test {t}" for t in sorted(test_agg.index)]
        test_scores = [float(test_agg[t]) for t in sorted(test_agg.index)]

        return {
            'student': student,
            'avg_percentage': avg_percentage,
            'total_tests_taken': total_tests,
            'subject_performance': subj_agg.to_dict(orient='records'),
            'test_trend': {
                'labels': test_labels,
                'scores': test_scores
            },
            'passed_all': passed_all
        }
