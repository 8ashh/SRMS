from services.student_service import StudentService

def test_add_student_valid(app):
    with app.app_context():
        student, err = StudentService.create_student("AI25099", "Ankit Verma", 3, "A")
        assert err == ""
        assert student is not None
        assert student.roll_no == "AI25099"
        assert student.name == "Ankit Verma"

def test_add_student_duplicate_roll_rejection(app, init_sample_data):
    with app.app_context():
        student, err = StudentService.create_student("ST001", "Another Student", 2, "A")
        assert student is None
        assert "already exists" in err

def test_add_student_invalid_roll(app):
    with app.app_context():
        # Disallow spaces or special characters in roll number
        student, err = StudentService.create_student("AI 25@99", "Ankit Verma", 3, "A")
        assert student is None
        assert "letters and digits only" in err

def test_add_student_invalid_semester(app):
    with app.app_context():
        student, err = StudentService.create_student("AI25100", "Ankit Verma", 9, "A")
        assert student is None
        assert "between 1 and 8" in err

def test_edit_and_delete_student(app, init_sample_data):
    with app.app_context():
        student = StudentService.get_by_roll_no("ST001")
        assert student is not None

        updated, err = StudentService.update_student(student.student_id, "ST001", "Student One Updated", 3, "B")
        assert err == ""
        assert updated.name == "Student One Updated"
        assert updated.semester == 3

        # Delete
        success, err = StudentService.delete_student(student.student_id)
        assert success is True
        assert StudentService.get_by_id(student.student_id) is None
