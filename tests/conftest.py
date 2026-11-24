import pytest
from app import create_app
from config import TestConfig
from extensions import db
from models import User, Student, Subject, Mark, Attendance

@pytest.fixture
def app():
    app = create_app(TestConfig)
    with app.app_context():
        db.create_all()
        yield app
        db.session.remove()
        db.drop_all()

@pytest.fixture
def client(app):
    return app.test_client()

@pytest.fixture
def runner(app):
    return app.test_cli_runner()

@pytest.fixture
def init_sample_data(app):
    """Seed minimal test data for testing services and routes."""
    with app.app_context():
        # Admin
        admin = User(username='admin', role='admin', faculty_name='Admin Test')
        admin.set_password('admin123')
        db.session.add(admin)

        # Faculty
        faculty = User(username='faculty1', role='faculty', faculty_name='Faculty Test')
        faculty.set_password('faculty123')
        db.session.add(faculty)

        # Subjects
        s1 = Subject(code='CS101', name='Intro to CS')
        s2 = Subject(code='CS102', name='Data Structures')
        db.session.add_all([s1, s2])
        db.session.flush()

        # Students
        st1 = Student(roll_no='ST001', name='Student One', semester=2, section='A')
        st2 = Student(roll_no='ST002', name='Student Two', semester=2, section='A')
        st3 = Student(roll_no='ST003', name='Student Three', semester=2, section='A')
        st4 = Student(roll_no='ST004', name='Student Four', semester=2, section='A')
        db.session.add_all([st1, st2, st3, st4])
        db.session.flush()

        # Student accounts
        u_st1 = User(username='st001', role='student', student_id=st1.student_id)
        u_st1.set_password('st001@123')
        u_st2 = User(username='st002', role='student', student_id=st2.student_id)
        u_st2.set_password('st002@123')
        db.session.add_all([u_st1, u_st2])

        # Marks
        m1 = Mark(student_id=st1.student_id, subject_id=s1.subject_id, test_no=1, score=45.0, max_score=50.0)
        m2 = Mark(student_id=st2.student_id, subject_id=s1.subject_id, test_no=1, score=40.0, max_score=50.0)
        m3 = Mark(student_id=st3.student_id, subject_id=s1.subject_id, test_no=1, score=38.0, max_score=50.0)
        m4 = Mark(student_id=st4.student_id, subject_id=s1.subject_id, test_no=1, score=15.0, max_score=50.0) # low outlier

        # Student 1 Test 2 (declining)
        m1_t2 = Mark(student_id=st1.student_id, subject_id=s1.subject_id, test_no=2, score=25.0, max_score=50.0) # drop from 90% to 50%
        db.session.add_all([m1, m2, m3, m4, m1_t2])

        db.session.commit()
