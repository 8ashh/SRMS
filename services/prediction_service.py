import os
import joblib
import numpy as np
import pandas as pd
from sklearn.linear_model import LinearRegression
from sklearn.ensemble import RandomForestRegressor
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_absolute_error, r2_score
from flask import current_app
from extensions import db
from models import Student, Mark, Attendance
from services.attendance_service import AttendanceService

MODEL_DIR = os.path.join(os.path.abspath(os.path.dirname(__file__)), '..', 'instance', 'ml_models')
os.makedirs(MODEL_DIR, exist_ok=True)
MODEL_FILE = os.path.join(MODEL_DIR, 'grade_predictor.joblib')

class PredictionService:
    """
    Predictive Grade Modelling Service.
    Uses Scikit-Learn (Linear Regression & Random Forest) to forecast student final performance
    based on Mid-term assessments and Attendance percentages.
    """

    _active_model = None
    _model_metadata = None

    @staticmethod
    def generate_synthetic_demo_dataset(n_samples=120, random_state=42):
        """
        Generates clearly labelled synthetic benchmark dataset for viva/demonstration purposes
        when historical labelled examination data is limited.
        Formula incorporates realistic academic correlation:
        Final % = 0.55 * Midterm % + 0.35 * Attendance % + random_noise (-5 to +5)
        """
        np.random.seed(random_state)
        midterm = np.random.uniform(35, 95, n_samples)
        attendance = np.random.uniform(50, 100, n_samples)
        noise = np.random.normal(0, 4.0, n_samples)
        
        # Real-world academic weighted relationship
        final = 0.55 * midterm + 0.35 * attendance + noise
        final = np.clip(final, 0.0, 100.0)

        df = pd.DataFrame({
            'midterm_score': np.round(midterm, 2),
            'attendance_rate': np.round(attendance, 2),
            'final_score': np.round(final, 2)
        })
        return df

    @staticmethod
    def extract_training_dataset():
        """
        Attempts to extract labelled training instances from the actual SQLite database.
        Requires students with at least 2 tests (Test 1 as midterm, Test 2+ as final).
        """
        students = Student.query.all()
        data = []

        for s in students:
            marks = Mark.query.filter_by(student_id=s.student_id).order_by(Mark.test_no.asc()).all()
            if len(marks) >= 2:
                # Test 1 as midterm proxy, latest test as outcome proxy
                midterm_pct = marks[0].percentage
                final_pct = marks[-1].percentage
                att_info = AttendanceService.calculate_student_attendance(s.student_id)
                att_pct = att_info['percentage'] if att_info['total'] > 0 else 75.0

                data.append({
                    'midterm_score': midterm_pct,
                    'attendance_rate': att_pct,
                    'final_score': final_pct
                })

        if len(data) >= 15:
            return pd.DataFrame(data), False  # Real data
        else:
            return None, True  # Insufficient data

    @staticmethod
    def train_model(force_demo=False, model_type='linear'):
        """
        Trains either Linear Regression or Random Forest Regressor.
        Evaluates with 80/20 train/test split using MAE and R² score.
        """
        real_df, is_insufficient = PredictionService.extract_training_dataset()

        if is_insufficient or force_demo:
            df = PredictionService.generate_synthetic_demo_dataset()
            data_source = "Synthetic Demonstration Benchmark (Labelled Synthetic Cohort, N=120)"
            is_demo = True
        else:
            df = real_df
            data_source = f"Empirical Database Records (N={len(df)} Students)"
            is_demo = False

        X = df[['midterm_score', 'attendance_rate']].values
        y = df['final_score'].values

        # 80/20 Split
        X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

        # Train Linear Regression
        lr_model = LinearRegression()
        lr_model.fit(X_train, y_train)
        lr_pred = lr_model.predict(X_test)
        lr_mae = float(round(mean_absolute_error(y_test, lr_pred), 3))
        lr_r2 = float(round(r2_score(y_test, lr_pred), 3))

        # Train Random Forest Regressor
        rf_model = RandomForestRegressor(n_estimators=60, max_depth=5, random_state=42)
        rf_model.fit(X_train, y_train)
        rf_pred = rf_model.predict(X_test)
        rf_mae = float(round(mean_absolute_error(y_test, rf_pred), 3))
        rf_r2 = float(round(r2_score(y_test, rf_pred), 3))

        # Pick selected model
        if model_type == 'random_forest':
            chosen_model = rf_model
            active_mae = rf_mae
            active_r2 = rf_r2
            model_name = "Random Forest Regressor"
        else:
            chosen_model = lr_model
            active_mae = lr_mae
            active_r2 = lr_r2
            model_name = "Linear Regression"

        metadata = {
            'model_name': model_name,
            'model_type': model_type,
            'data_source': data_source,
            'is_demo': is_demo,
            'sample_size': len(df),
            'train_size': len(X_train),
            'test_size': len(X_test),
            'mae': active_mae,
            'r2_score': active_r2,
            'comparison': {
                'linear_regression': {'mae': lr_mae, 'r2': lr_r2},
                'random_forest': {'mae': rf_mae, 'r2': rf_r2}
            }
        }

        # Cache model & save to disk
        PredictionService._active_model = chosen_model
        PredictionService._model_metadata = metadata

        try:
            joblib.dump({'model': chosen_model, 'metadata': metadata}, MODEL_FILE)
        except Exception as e:
            print(f"[PredictionService] Warning: Could not persist model to disk: {e}")

        return metadata

    @staticmethod
    def get_or_load_model():
        """Ensure an active model exists in memory or load from disk."""
        if PredictionService._active_model is not None:
            return PredictionService._active_model, PredictionService._model_metadata

        if os.path.exists(MODEL_FILE):
            try:
                saved = joblib.load(MODEL_FILE)
                PredictionService._active_model = saved['model']
                PredictionService._model_metadata = saved['metadata']
                return PredictionService._active_model, PredictionService._model_metadata
            except Exception:
                pass

        # If not saved, initialize model
        PredictionService.train_model(force_demo=True, model_type='linear')
        return PredictionService._active_model, PredictionService._model_metadata

    @staticmethod
    def score_to_grade(score):
        """Converts numerical score to letter grade based on configurable cutoffs."""
        cutoffs = current_app.config.get('GRADE_CUTOFFS', {
            'A': 75.0, 'B': 60.0, 'C': 40.0, 'F': 0.0
        }) if current_app else {'A': 75.0, 'B': 60.0, 'C': 40.0, 'F': 0.0}

        if score >= cutoffs['A']:
            return 'A', 'success'
        elif score >= cutoffs['B']:
            return 'B', 'primary'
        elif score >= cutoffs['C']:
            return 'C', 'warning'
        else:
            return 'F', 'danger'

    @staticmethod
    def predict_for_student(student_id):
        """
        Generates predicted final score and grade for a given student.
        Uses student's average mid-term marks and overall attendance.
        """
        student = Student.query.get(student_id)
        if not student:
            return None

        # Fetch midterms (Test 1 or average marks available)
        marks = Mark.query.filter_by(student_id=student_id).all()
        if not marks:
            return {
                'student_id': student_id,
                'student_name': student.name,
                'roll_no': student.roll_no,
                'status': 'unavailable',
                'message': 'No test marks recorded yet for this student.'
            }

        midterm_avg = round(float(np.mean([m.percentage for m in marks])), 2)

        # Fetch attendance
        att_info = AttendanceService.calculate_student_attendance(student_id)
        att_pct = att_info['percentage']

        model, metadata = PredictionService.get_or_load_model()
        if not model:
            return {
                'student_id': student_id,
                'student_name': student.name,
                'roll_no': student.roll_no,
                'status': 'unavailable',
                'message': 'Prediction model is currently unavailable.'
            }

        # Predict
        input_features = np.array([[midterm_avg, att_pct]])
        predicted_score = float(model.predict(input_features)[0])
        predicted_score = max(0.0, min(100.0, round(predicted_score, 2)))

        grade, badge_class = PredictionService.score_to_grade(predicted_score)

        return {
            'student_id': student_id,
            'student_name': student.name,
            'roll_no': student.roll_no,
            'semester': student.semester,
            'section': student.section,
            'midterm_avg': midterm_avg,
            'attendance_rate': att_pct,
            'predicted_score': predicted_score,
            'predicted_grade': grade,
            'badge_class': badge_class,
            'model_name': metadata.get('model_name', 'Linear Regression'),
            'data_source': metadata.get('data_source', 'Synthetic Demonstration Benchmark'),
            'is_demo': metadata.get('is_demo', True),
            'model_mae': metadata.get('mae', 0.0),
            'model_r2': metadata.get('r2_score', 0.0),
            'status': 'success',
            'disclaimer': "Notice: This estimation is an academic guidance indicator generated via statistical regression. It is not an official guarantee of final semester examination results."
        }

    @staticmethod
    def get_all_predictions(semester=None, section=None):
        """Generates predictions for all enrolled students in cohort."""
        query = Student.query
        if semester:
            query = query.filter(Student.semester == int(semester))
        if section:
            query = query.filter(Student.section == section)

        students = query.order_by(Student.roll_no.asc()).all()
        predictions = []
        for s in students:
            pred = PredictionService.predict_for_student(s.student_id)
            if pred and pred.get('status') == 'success':
                predictions.append(pred)

        return predictions
