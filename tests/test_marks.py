from services.marks_service import MarksService

def test_marks_valid_and_percentage_calculation(app, init_sample_data):
    with app.app_context():
        # Score 35 / 50 -> 70.0%
        mark, err = MarksService.record_mark(student_id=2, subject_id=2, test_no=1, score=35.0, max_score=50.0)
        assert err == ""
        assert mark is not None
        assert mark.percentage == 70.0

def test_negative_marks_rejection(app, init_sample_data):
    with app.app_context():
        mark, err = MarksService.record_mark(student_id=2, subject_id=2, test_no=2, score=-5.0, max_score=50.0)
        assert mark is None
        assert "cannot be negative" in err

def test_score_exceeds_max_rejection(app, init_sample_data):
    with app.app_context():
        mark, err = MarksService.record_mark(student_id=2, subject_id=2, test_no=2, score=55.0, max_score=50.0)
        assert mark is None
        assert "cannot exceed maximum score" in err

def test_duplicate_test_marks_rejection(app, init_sample_data):
    with app.app_context():
        # Student 1 already has Test 1 for Subject 1 in init_sample_data
        mark, err = MarksService.record_mark(student_id=1, subject_id=1, test_no=1, score=40.0, max_score=50.0)
        assert mark is None
        assert "already exists" in err

def test_update_and_delete_marks(app, init_sample_data):
    with app.app_context():
        marks_list = MarksService.get_student_marks(1)
        target = marks_list[0]

        updated, err = MarksService.update_mark(target.mark_id, score=48.0, max_score=50.0)
        assert err == ""
        assert updated.score == 48.0
        assert updated.percentage == 96.0

        # Delete
        success, err = MarksService.delete_mark(target.mark_id)
        assert success is True
        assert MarksService.get_by_id(target.mark_id) is None
