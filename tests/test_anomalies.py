from services.anomaly_service import AnomalyService

def test_anomaly_detection_methods(app, init_sample_data):
    with app.app_context():
        # In init_sample_data:
        # Student 1: Test 1 was 45/50 (90%), Test 2 was 25/50 (50%) -> drop of 40% (exceeds 15% threshold)
        # Student 4: Test 1 was 15/50 (30%), while cohort mean is (45+40+38+15)/4 = 34.5/50 (69%)
        # Student 4 should be flagged by Z-score, Student 1 by falling performance drop.
        alerts = AnomalyService.detect_anomalies()
        assert len(alerts) >= 1

        alert_students = [a['roll_no'] for a in alerts]
        assert ('ST001' in alert_students) or ('ST004' in alert_students)

        # Check falling trend reason text
        st1_alerts = [a for a in alerts if a['roll_no'] == 'ST001']
        if st1_alerts:
            assert "decline" in st1_alerts[0]['reason'].lower() or "dropped" in st1_alerts[0]['reason'].lower()
