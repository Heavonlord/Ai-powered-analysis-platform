"""
AttendAI — Test Suite
Run: python -m pytest tests/ -v
"""
import pytest
import json
from datetime import date, timedelta
from app import create_app, db
from app.models import User, Course, Enrollment, Attendance


@pytest.fixture
def app():
    app = create_app('testing')
    with app.app_context():
        db.create_all()
        yield app
        db.session.remove()
        db.drop_all()


@pytest.fixture
def client(app):
    return app.test_client()


@pytest.fixture
def seeded_app(app):
    """App with pre-seeded admin, teacher, student, course, and enrollments."""
    with app.app_context():
        admin = User(username='admin', email='admin@test.com', role='admin')
        admin.set_password('admin123')

        teacher = User(username='teacher1', email='teacher@test.com', role='teacher')
        teacher.set_password('teacher123')

        student = User(username='student1', email='student@test.com',
                       role='student', roll_no='CS101',
                       parent_phone='+919876543210', parent_email='parent@test.com')
        student.set_password('student123')

        db.session.add_all([admin, teacher, student])
        db.session.flush()

        course = Course(name='Data Structures', code='CS301', teacher_id=teacher.id)
        db.session.add(course)
        db.session.flush()

        enrollment = Enrollment(student_id=student.id, course_id=course.id)
        db.session.add(enrollment)
        db.session.commit()

    return app


# ─── Helper ────────────────────────────────────────────────────
def login(client, username, password):
    return client.post('/login', data={'username': username, 'password': password},
                       follow_redirects=True)


# ─── Auth Tests ────────────────────────────────────────────────
class TestAuth:
    def test_login_page_loads(self, client):
        r = client.get('/login')
        assert r.status_code == 200
        assert b'AttendAI' in r.data

    def test_index_redirects_to_login(self, client):
        r = client.get('/', follow_redirects=False)
        # If not authenticated, either shows landing or redirects
        assert r.status_code in (200, 302)

    def test_admin_login(self, seeded_app):
        client = seeded_app.test_client()
        r = login(client, 'admin', 'admin123')
        assert b'Admin Dashboard' in r.data or b'admin' in r.data.lower()

    def test_teacher_login(self, seeded_app):
        client = seeded_app.test_client()
        r = login(client, 'teacher1', 'teacher123')
        assert r.status_code == 200

    def test_student_login(self, seeded_app):
        client = seeded_app.test_client()
        r = login(client, 'student1', 'student123')
        assert r.status_code == 200

    def test_invalid_login(self, seeded_app):
        client = seeded_app.test_client()
        r = login(client, 'admin', 'wrongpassword')
        assert b'Invalid' in r.data or b'invalid' in r.data.lower()

    def test_logout(self, seeded_app):
        client = seeded_app.test_client()
        login(client, 'admin', 'admin123')
        r = client.get('/logout', follow_redirects=True)
        assert r.status_code == 200


# ─── Model Tests ───────────────────────────────────────────────
class TestModels:
    def test_user_password_hashing(self, app):
        with app.app_context():
            u = User(username='test', email='test@t.com', role='student')
            u.set_password('secret')
            assert u.check_password('secret') is True
            assert u.check_password('wrong') is False

    def test_attendance_percentage_empty(self, seeded_app):
        with seeded_app.app_context():
            student = User.query.filter_by(username='student1').first()
            assert student.get_attendance_percentage() == 0

    def test_attendance_percentage_calculation(self, seeded_app):
        with seeded_app.app_context():
            student = User.query.filter_by(username='student1').first()
            course = Course.query.filter_by(code='CS301').first()

            # Add 10 present, 2 absent
            for i in range(12):
                status = 'present' if i < 10 else 'absent'
                db.session.add(Attendance(
                    student_id=student.id, course_id=course.id,
                    date=date.today() - timedelta(days=i),
                    status=status
                ))
            db.session.commit()

            pct = student.get_attendance_percentage(course.id)
            assert abs(pct - 83.3) < 0.5

    def test_risk_level_safe(self, seeded_app):
        with seeded_app.app_context():
            student = User.query.filter_by(username='student1').first()
            course = Course.query.filter_by(code='CS301').first()
            # 9 present out of 10 = 90%
            for i in range(10):
                db.session.add(Attendance(
                    student_id=student.id, course_id=course.id,
                    date=date.today() - timedelta(days=i),
                    status='present' if i < 9 else 'absent'
                ))
            db.session.commit()
            risk, color = student.get_risk_level(course.id)
            assert risk == 'SAFE'
            assert color == 'success'

    def test_risk_level_critical(self, seeded_app):
        with seeded_app.app_context():
            student = User.query.filter_by(username='student1').first()
            course = Course.query.filter_by(code='CS301').first()
            # 5 present out of 10 = 50%
            for i in range(10):
                db.session.add(Attendance(
                    student_id=student.id, course_id=course.id,
                    date=date.today() - timedelta(days=i),
                    status='present' if i < 5 else 'absent'
                ))
            db.session.commit()
            risk, _ = student.get_risk_level(course.id)
            assert risk == 'CRITICAL'

    def test_can_miss_calculation(self, seeded_app):
        with seeded_app.app_context():
            student = User.query.filter_by(username='student1').first()
            course = Course.query.filter_by(code='CS301').first()
            # 9/10 = 90% — should be able to miss some
            for i in range(10):
                db.session.add(Attendance(
                    student_id=student.id, course_id=course.id,
                    date=date.today() - timedelta(days=i),
                    status='present' if i < 9 else 'absent'
                ))
            db.session.commit()
            can_miss, needed = student.get_can_miss(course.id)
            assert can_miss >= 0
            assert needed == 0

    def test_course_enrolled_students(self, seeded_app):
        with seeded_app.app_context():
            course = Course.query.filter_by(code='CS301').first()
            students = course.get_enrolled_students()
            assert len(students) == 1
            assert students[0].username == 'student1'


# ─── Admin Route Tests ─────────────────────────────────────────
class TestAdminRoutes:
    def test_admin_dashboard_accessible(self, seeded_app):
        client = seeded_app.test_client()
        login(client, 'admin', 'admin123')
        r = client.get('/admin')
        assert r.status_code == 200

    def test_teacher_cannot_access_admin(self, seeded_app):
        client = seeded_app.test_client()
        login(client, 'teacher1', 'teacher123')
        r = client.get('/admin', follow_redirects=True)
        assert b'Access denied' in r.data or r.status_code in (302, 403)

    def test_add_user(self, seeded_app):
        client = seeded_app.test_client()
        login(client, 'admin', 'admin123')
        r = client.post('/admin/users/add', data={
            'username': 'newstudent',
            'email': 'new@test.com',
            'password': 'Pass@1234',
            'role': 'student',
            'roll_no': 'CS999',
        }, follow_redirects=True)
        assert r.status_code == 200
        with seeded_app.app_context():
            assert User.query.filter_by(username='newstudent').first() is not None

    def test_add_course(self, seeded_app):
        client = seeded_app.test_client()
        login(client, 'admin', 'admin123')
        with seeded_app.app_context():
            teacher = User.query.filter_by(username='teacher1').first()
            tid = teacher.id
        r = client.post('/admin/courses/add', data={
            'name': 'New Course',
            'code': 'CS999',
            'teacher_id': tid,
        }, follow_redirects=True)
        assert r.status_code == 200
        with seeded_app.app_context():
            assert Course.query.filter_by(code='CS999').first() is not None

    def test_admin_analytics(self, seeded_app):
        client = seeded_app.test_client()
        login(client, 'admin', 'admin123')
        r = client.get('/admin/analytics')
        assert r.status_code == 200

    def test_csv_template_download(self, seeded_app):
        client = seeded_app.test_client()
        login(client, 'admin', 'admin123')
        r = client.get('/admin/csv-template')
        assert r.status_code == 200
        assert b'username' in r.data


# ─── Teacher Route Tests ───────────────────────────────────────
class TestTeacherRoutes:
    def test_teacher_dashboard(self, seeded_app):
        client = seeded_app.test_client()
        login(client, 'teacher1', 'teacher123')
        r = client.get('/teacher')
        assert r.status_code == 200

    def test_mark_attendance_page(self, seeded_app):
        client = seeded_app.test_client()
        login(client, 'teacher1', 'teacher123')
        with seeded_app.app_context():
            course = Course.query.filter_by(code='CS301').first()
            cid = course.id
        r = client.get(f'/teacher/course/{cid}/attendance')
        assert r.status_code == 200

    def test_mark_attendance_post(self, seeded_app):
        client = seeded_app.test_client()
        login(client, 'teacher1', 'teacher123')
        with seeded_app.app_context():
            course = Course.query.filter_by(code='CS301').first()
            student = User.query.filter_by(username='student1').first()
            cid, sid = course.id, student.id

        r = client.post(f'/teacher/course/{cid}/attendance', data={
            'date': date.today().isoformat(),
            f'status_{sid}': 'present',
        }, follow_redirects=True)
        assert r.status_code == 200

        with seeded_app.app_context():
            att = Attendance.query.filter_by(student_id=sid, course_id=cid, date=date.today()).first()
            assert att is not None
            assert att.status == 'present'

    def test_course_analytics(self, seeded_app):
        client = seeded_app.test_client()
        login(client, 'teacher1', 'teacher123')
        with seeded_app.app_context():
            course = Course.query.filter_by(code='CS301').first()
            cid = course.id
        r = client.get(f'/teacher/course/{cid}/analytics')
        assert r.status_code == 200

    def test_manage_enrollments(self, seeded_app):
        client = seeded_app.test_client()
        login(client, 'teacher1', 'teacher123')
        with seeded_app.app_context():
            course = Course.query.filter_by(code='CS301').first()
            cid = course.id
        r = client.get(f'/teacher/course/{cid}/enrollments')
        assert r.status_code == 200

    def test_qr_display(self, seeded_app):
        client = seeded_app.test_client()
        login(client, 'teacher1', 'teacher123')
        with seeded_app.app_context():
            course = Course.query.filter_by(code='CS301').first()
            cid = course.id
        r = client.get(f'/teacher/course/{cid}/qr')
        assert r.status_code == 200
        assert b'QR' in r.data


# ─── Student Route Tests ───────────────────────────────────────
class TestStudentRoutes:
    def test_student_dashboard(self, seeded_app):
        client = seeded_app.test_client()
        login(client, 'student1', 'student123')
        r = client.get('/student')
        assert r.status_code == 200

    def test_student_cannot_access_teacher_routes(self, seeded_app):
        client = seeded_app.test_client()
        login(client, 'student1', 'student123')
        with seeded_app.app_context():
            course = Course.query.filter_by(code='CS301').first()
            cid = course.id
        r = client.get(f'/teacher/course/{cid}/analytics', follow_redirects=True)
        assert b'Access denied' in r.data or r.status_code in (302, 403)

    def test_scan_qr_page(self, seeded_app):
        client = seeded_app.test_client()
        login(client, 'student1', 'student123')
        r = client.get('/scan-qr')
        assert r.status_code == 200

    def test_qr_scan_invalid_token(self, seeded_app):
        client = seeded_app.test_client()
        login(client, 'student1', 'student123')
        r = client.post('/api/qr/scan',
                        data=json.dumps({'token': 'invalid_token'}),
                        content_type='application/json')
        data = json.loads(r.data)
        assert data['success'] is False


# ─── Analytics Tests ───────────────────────────────────────────
class TestAnalytics:
    def test_predict_no_data(self, seeded_app):
        with seeded_app.app_context():
            from app.utils.analytics import predict_future_attendance
            student = User.query.filter_by(username='student1').first()
            course = Course.query.filter_by(code='CS301').first()
            result = predict_future_attendance(student.id, course.id, db, Attendance)
            assert result is None  # Not enough data

    def test_predict_with_data(self, seeded_app):
        with seeded_app.app_context():
            from app.utils.analytics import predict_future_attendance
            student = User.query.filter_by(username='student1').first()
            course = Course.query.filter_by(code='CS301').first()
            # Add 15 classes
            for i in range(15):
                db.session.add(Attendance(
                    student_id=student.id, course_id=course.id,
                    date=date.today() - timedelta(days=i),
                    status='present' if i % 5 != 0 else 'absent'
                ))
            db.session.commit()
            result = predict_future_attendance(student.id, course.id, db, Attendance)
            assert result is not None
            assert 0 <= result['predicted_pct'] <= 100

    def test_get_attendance_trend(self, seeded_app):
        with seeded_app.app_context():
            from app.utils.analytics import get_attendance_trend
            student = User.query.filter_by(username='student1').first()
            course = Course.query.filter_by(code='CS301').first()
            for i in range(5):
                db.session.add(Attendance(
                    student_id=student.id, course_id=course.id,
                    date=date.today() - timedelta(days=i),
                    status='present'
                ))
            db.session.commit()
            trend = get_attendance_trend(student.id, course.id, db, Attendance)
            assert len(trend) == 5
            assert all('date' in t and 'pct' in t for t in trend)

    def test_weekly_pattern(self, seeded_app):
        with seeded_app.app_context():
            from app.utils.analytics import get_weekly_pattern
            student = User.query.filter_by(username='student1').first()
            course = Course.query.filter_by(code='CS301').first()
            for i in range(14):
                db.session.add(Attendance(
                    student_id=student.id, course_id=course.id,
                    date=date.today() - timedelta(days=i),
                    status='present'
                ))
            db.session.commit()
            pattern = get_weekly_pattern(student.id, course.id, db, Attendance)
            assert isinstance(pattern, dict)
