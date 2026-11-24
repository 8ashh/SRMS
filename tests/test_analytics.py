from services.analytics_service import AnalyticsService

def test_analytics_kpi_and_subject_averages(app, init_sample_data):
    with app.app_context():
        summary = AnalyticsService.get_overall_summary()
        assert summary['total_students'] == 4
        assert summary['total_subjects'] == 2
        assert summary['total_marks_records'] == 5
        assert summary['overall_avg_percentage'] > 0

        # Subject averages
        subj_avg = AnalyticsService.get_subject_averages()
        assert 'CS101' in subj_avg['labels']
        assert len(subj_avg['averages']) > 0

def test_grade_distribution_and_pass_fail(app, init_sample_data):
    with app.app_context():
        grade_dist = AnalyticsService.get_grade_distribution()
        assert grade_dist['total'] == 5
        assert 'A' in grade_dist['raw_counts']
        assert 'F' in grade_dist['raw_counts']

        pass_fail = AnalyticsService.get_pass_fail_stats()
        assert pass_fail['passed'] >= 1
        assert pass_fail['failed'] >= 1
        assert pass_fail['pass_rate'] > 0
