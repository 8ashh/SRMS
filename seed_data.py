import random
from datetime import datetime, date, timedelta
from app import create_app
from extensions import db
from models import User, Student, Subject, Mark, Attendance, AuditLog
from services.prediction_service import PredictionService

def seed_database(reset=True, app=None):
    if app is None:
        app = create_app()
    with app.app_context():
        if reset:
            print("[Seed] Resetting database tables...")
            db.drop_all()
            db.create_all()

        print("[Seed] Creating administrative and faculty accounts...")
        # 1. Admin
        admin = User(
            username='admin',
            role='admin',
            faculty_name='System Administrator'
        )
        admin.set_password('admin123')
        db.session.add(admin)

        # 2. Faculty
        faculty1 = User(
            username='faculty_sharma',
            role='faculty',
            faculty_name='Dr. Rajesh Sharma'
        )
        faculty1.set_password('faculty123')
        db.session.add(faculty1)

        faculty2 = User(
            username='faculty_verma',
            role='faculty',
            faculty_name='Prof. Sunita Verma'
        )
        faculty2.set_password('faculty123')
        db.session.add(faculty2)

        # 3. Subjects
        print("[Seed] Inserting curriculum subjects...")
        subjects_data = [
            ('CS201', 'Data Structures & Algorithms'),
            ('CS202', 'Discrete Mathematics'),
            ('CS203', 'Computer Architecture'),
            ('CS204', 'Object Oriented Programming'),
            ('CS205', 'Database Management Systems')
        ]
        subject_objects = []
        for code, name in subjects_data:
            subj = Subject(code=code, name=name)
            db.session.add(subj)
            subject_objects.append(subj)

        db.session.flush()

        # 4. Students (24 fictional students)
        print("[Seed] Enrolling 24 fictional students...")
        student_names = [
            ("AI23001", "Rahul Sharma", 4, "A"),
            ("AI23002", "Priya Patel", 4, "A"),
            ("AI23003", "Amit Kumar", 4, "A"),
            ("AI23004", "Ananya Singh", 4, "A"),
            ("AI23005", "Rohan Gupta", 4, "A"),    # Declining performance profile
            ("AI23006", "Sneha Joshi", 4, "A"),
            ("AI23007", "Karan Malhotra", 4, "A"),
            ("AI23008", "Neha Reddy", 4, "A"),
            ("AI23009", "Vikram Meena", 4, "A"),   # Outlier low score (Z < -1.5)
            ("AI23010", "Aditi Rao", 4, "A"),
            ("AI23011", "Manish Saxena", 4, "A"),
            ("AI23012", "Pooja Tiwari", 4, "A"),   # Low attendance profile
            ("AI23013", "Siddharth Jain", 4, "B"),
            ("AI23014", "Deepika Mishra", 4, "B"),
            ("AI23015", "Gaurav Sen", 4, "B"),
            ("AI23016", "Divya Agarwal", 4, "B"),
            ("AI23017", "Mohit Yadav", 4, "B"),
            ("AI23018", "Shweta Pandey", 4, "B"),
            ("AI23019", "Arjun Nair", 4, "B"),
            ("AI23020", "Megha Kapoor", 4, "B"),
            ("AI23021", "Harsh Vardhan", 4, "B"),
            ("AI23022", "Ritu Choudhary", 4, "B"),
            ("AI23023", "Naveen Dubey", 4, "B"),
            ("AI23024", "Kavita Bisht", 4, "B")
        ]

        student_objects = []
        for roll, name, sem, sec in student_names:
            st = Student(roll_no=roll, name=name, semester=sem, section=sec)
            db.session.add(st)
            db.session.flush()

            # Provision linked student account
            st_user = User(
                username=roll.lower(),
                role='student',
                student_id=st.student_id
            )
            st_user.set_password(f"{roll}@123")
            db.session.add(st_user)

            student_objects.append(st)

        db.session.flush()

        # 5. Insert Marks (Test 1, Test 2, Test 3)
        print("[Seed] Recording assessment test marks...")
        random.seed(42)

        for s in student_objects:
            is_declining = (s.roll_no == 'AI23005')
            is_low_performer = (s.roll_no == 'AI23009')
            is_star = (s.roll_no in ('AI23001', 'AI23002'))

            for subj in subject_objects:
                for test_no in [1, 2, 3]:
                    max_score = 50.0

                    if is_declining:
                        # Drops sharply across tests: T1=42, T2=30, T3=19
                        if test_no == 1:
                            score = 42.0
                        elif test_no == 2:
                            score = 30.0  # drop of 24%
                        else:
                            score = 19.0  # drop of 22%
                    elif is_low_performer:
                        # Consistently low (12-16 out of 50 -> Z < -1.5)
                        score = float(random.choice([12, 13, 14, 15, 16]))
                    elif is_star:
                        # High performance (42-48 out of 50)
                        score = float(random.randint(43, 49))
                    else:
                        # General realistic performance distribution
                        score = float(random.randint(28, 45))

                    mark = Mark(
                        student_id=s.student_id,
                        subject_id=subj.subject_id,
                        test_no=test_no,
                        score=score,
                        max_score=max_score
                    )
                    db.session.add(mark)

        # 6. Insert Attendance over 12 calendar lecture days
        print("[Seed] Logging daily classroom attendance records...")
        today = date.today()
        # Pick 12 working dates backwards (avoiding future dates)
        lecture_dates = []
        d = today
        while len(lecture_dates) < 12:
            if d.weekday() < 5:  # Monday to Friday
                lecture_dates.append(d)
            d -= timedelta(days=1)
        lecture_dates.reverse()

        for d_entry in lecture_dates:
            for subj in subject_objects:
                for s in student_objects:
                    is_low_att = (s.roll_no == 'AI23012')
                    is_star = (s.roll_no in ('AI23001', 'AI23002'))

                    if is_low_att:
                        status = 'Present' if random.random() < 0.45 else 'Absent'
                    elif is_star:
                        status = 'Present' if random.random() < 0.98 else 'Absent'
                    else:
                        status = 'Present' if random.random() < 0.82 else 'Absent'

                    att = Attendance(
                        student_id=s.student_id,
                        subject_id=subj.subject_id,
                        date=d_entry,
                        status=status
                    )
                    db.session.add(att)

        # 7. Initial Audit Log
        print("[Seed] Recording initialization audit log...")
        init_log = AuditLog(
            user_id=admin.user_id,
            action="SYSTEM_INITIALIZE",
            module="System",
            record_id="1",
            description="System initialized with institutional benchmark demo dataset for MITS Gwalior."
        )
        db.session.add(init_log)

        db.session.commit()
        print("[Seed] Database commit completed.")

        # 8. Train Initial Prediction Model
        print("[Seed] Training Scikit-learn predictive model...")
        PredictionService.train_model(force_demo=True, model_type='linear')
        print("[Seed] Seeding process successfully finalized!")

if __name__ == '__main__':
    seed_database()
