"""
Script to create admin user and optionally seed sample data.
Run: python create_admin.py
Run with sample data: python create_admin.py --seed
"""
import sys
from datetime import date, timedelta
import random

def create_admin():
    from app import create_app, db
    from app.models import User, Course, Enrollment, Attendance

    app = create_app('development')
    with app.app_context():
        db.create_all()

        # Create Admin
        if not User.query.filter_by(username='admin').first():
            admin = User(username='admin', email='admin@college.edu', role='admin', is_active=True)
            admin.set_password('admin123')
            db.session.add(admin)
            print("✅ Admin created: username=admin, password=admin123")
        else:
            print("ℹ️  Admin already exists")

        db.session.commit()

        if '--seed' in sys.argv:
            seed_sample_data(db, User, Course, Enrollment, Attendance)


def seed_sample_data(db, User, Course, Enrollment, Attendance):
    print("\n🌱 Seeding sample data...")

    # Create 3 teachers
    teachers = []
    for i in range(1, 4):
        u = User.query.filter_by(username=f'teacher{i}').first()
        if not u:
            u = User(username=f'teacher{i}', email=f'teacher{i}@college.edu',
                     role='teacher', is_active=True)
            u.set_password('teacher123')
            db.session.add(u)
        teachers.append(u)
    db.session.flush()
    print(f"✅ {len(teachers)} teachers ready")

    # Create 5 courses
    course_data = [
        ('Data Structures', 'CS301', 0),
        ('Database Systems', 'CS302', 0),
        ('Web Technologies', 'CS303', 1),
        ('Computer Networks', 'CS304', 1),
        ('Operating Systems', 'CS305', 2),
    ]
    courses = []
    for name, code, t_idx in course_data:
        c = Course.query.filter_by(code=code).first()
        if not c:
            c = Course(name=name, code=code, teacher_id=teachers[t_idx].id)
            db.session.add(c)
        courses.append(c)
    db.session.flush()
    print(f"✅ {len(courses)} courses ready")

    # Create 20 students
    students = []
    for i in range(1, 21):
        u = User.query.filter_by(username=f'student{i}').first()
        if not u:
            u = User(
                username=f'student{i}', email=f'student{i}@college.edu',
                role='student', is_active=True,
                roll_no=f'CS{100+i}',
                parent_phone=f'+9198765{43200+i:05d}',
                parent_email=f'parent{i}@example.com'
            )
            u.set_password('student123')
            db.session.add(u)
        students.append(u)
    db.session.flush()
    print(f"✅ {len(students)} students ready")

    # Enroll all students in all courses
    for s in students:
        for c in courses:
            if not Enrollment.query.filter_by(student_id=s.id, course_id=c.id).first():
                db.session.add(Enrollment(student_id=s.id, course_id=c.id))
    db.session.flush()
    print(f"✅ Enrollments created")

    # Generate 30 days of attendance with realistic patterns
    today = date.today()
    # Different students have different attendance patterns
    patterns = {
        'good': 0.92,     # 6 students - ≥90% attendance
        'average': 0.80,  # 8 students - ~80%
        'low': 0.70,      # 4 students - ~70% (caution)
        'critical': 0.55, # 2 students - <65% (critical)
    }
    pattern_list = (['good']*6 + ['average']*8 + ['low']*4 + ['critical']*2)

    for day_offset in range(30, 0, -1):
        att_date = today - timedelta(days=day_offset)
        if att_date.weekday() >= 5:  # Skip weekends
            continue
        for c in courses:
            for i, s in enumerate(students):
                pattern = pattern_list[i]
                prob = patterns[pattern]
                r = random.random()
                if r < prob:
                    status = 'present'
                elif r < prob + 0.05:
                    status = 'late'
                else:
                    status = 'absent'
                if not Attendance.query.filter_by(student_id=s.id, course_id=c.id, date=att_date).first():
                    db.session.add(Attendance(student_id=s.id, course_id=c.id, date=att_date, status=status))

    db.session.commit()
    print("✅ 30 days of attendance data generated")
    print("\n🎉 Sample data seeding complete!")
    print("\nDemo Accounts:")
    print("  Admin:    admin / admin123")
    print("  Teacher:  teacher1 / teacher123")
    print("  Student:  student1 / student123 (or student2...student20)")


if __name__ == '__main__':
    create_admin()
