from services.prediction_service import PredictionService

def test_prediction_training_and_metrics(app):
    with app.app_context():
        # Train Linear Regression model using synthetic benchmark dataset
        metadata = PredictionService.train_model(force_demo=True, model_type='linear')
        assert metadata['model_name'] == 'Linear Regression'
        assert metadata['mae'] >= 0.0
        assert metadata['r2_score'] <= 1.0
        assert metadata['train_size'] > 0

        # Train Random Forest Regressor
        rf_metadata = PredictionService.train_model(force_demo=True, model_type='random_forest')
        assert rf_metadata['model_name'] == 'Random Forest Regressor'
        assert rf_metadata['mae'] >= 0.0

def test_prediction_output_bounds_and_disclaimer(app, init_sample_data):
    with app.app_context():
        PredictionService.train_model(force_demo=True, model_type='linear')
        pred = PredictionService.predict_for_student(1)
        assert pred is not None
        assert pred['status'] == 'success'
        assert 0.0 <= pred['predicted_score'] <= 100.0
        assert pred['predicted_grade'] in ('A', 'B', 'C', 'F')
        assert "Notice" in pred['disclaimer']
