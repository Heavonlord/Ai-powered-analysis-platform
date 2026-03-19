from app import db, login_manager, bcrypt
from flask_login import UserMixin
from datetime import datetime


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


class User(UserMixin, db.Model):
    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False, index=True)
    email = db.Column(db.String(120), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(255), nullable=False)
    role = db.Column(db.String(20), nullable=False, default='student')  # admin/teacher/student
    roll_no = db.Column(db.String(20), unique=True, nullable=True, index=True)
    is_active = db.Column(db.Boolean, default=True)
    parent_phone = db.Column(db.String(20), nullable=True)
    parent_email = db.Column(db.String(120), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    failed_logins = db.Column(db.Integer, default=0)
    locked_until = db.Column(db.DateTime, nullable=True)

    # Relationships
    taught_courses = db.relationship('Course', backref='teacher', lazy='dynamic',
                                     foreign_keys='Course.teacher_id')
    enrollments = db.relationship('Enrollment', backref='student', lazy='dynamic',
                                  foreign_keys='Enrollment.student_id')
    attendance_records = db.relationship('Attendance', backref='student', lazy='dynamic',
                                         foreign_keys='Attendance.student_id')

    def set_password(self, password):
        self.password_hash = bcrypt.generate_password_hash(password).decode('utf-8')

    def check_password(self, password):
        return bcrypt.check_password_hash(self.password_hash, password)

    def get_attendance_percentage(self, course_id=None):
        query = Attendance.query.filter_by(student_id=self.id)
        if course_id:
            query = query.filter_by(course_id=course_id)
        total = query.count()
        if total == 0:
            return 0
        present = query.filter(Attendance.status.in_(['present', 'late'])).count()
        return round((present / total) * 100, 1)

    def get_risk_level(self, course_id=None):
        pct = self.get_attendance_percentage(course_id)
        if pct >= 80:
            return 'SAFE', 'success'
        elif pct >= 75:
            return 'CAUTION', 'warning'
        elif pct >= 65:
            return 'WARNING', 'orange'
        else:
            return 'CRITICAL', 'danger'

    def get_can_miss(self, course_id=None):
        """Calculate how many classes student can still miss while staying above 75%"""
        query = Attendance.query.filter_by(student_id=self.id)
        if course_id:
            query = query.filter_by(course_id=course_id)
        total = query.count()
        present = query.filter(Attendance.status.in_(['present', 'late'])).count()
        absent = total - present
        if total == 0:
            return 0, 0

        from math import floor, ceil
        # max_absences such that present/(present+max_absences) >= 0.75
        max_absences = floor(present / 3)  # solve: present/(present+x) >= 0.75 => x <= present/3
        can_miss = max(0, max_absences - absent)

        # classes needed if below 75%
        if present / total < 0.75:
            classes_needed = ceil(0.75 * total - present) + 1
        else:
            classes_needed = 0
        return can_miss, classes_needed

    def __repr__(self):
        return f'<User {self.username} ({self.role})>'


class Course(db.Model):
    __tablename__ = 'courses'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), nullable=False)
    code = db.Column(db.String(20), unique=True, nullable=False, index=True)
    teacher_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    enrollments = db.relationship('Enrollment', backref='course', lazy='dynamic')
    attendance_records = db.relationship('Attendance', backref='course', lazy='dynamic')

    def get_enrolled_students(self):
        enrollment_ids = [e.student_id for e in self.enrollments]
        return User.query.filter(User.id.in_(enrollment_ids)).all()

    def get_total_classes(self):
        from sqlalchemy import func
        result = db.session.query(func.count(func.distinct(Attendance.date))) \
            .filter_by(course_id=self.id).scalar()
        return result or 0

    def get_avg_attendance(self):
        students = self.get_enrolled_students()
        if not students:
            return 0
        total = sum(s.get_attendance_percentage(self.id) for s in students)
        return round(total / len(students), 1)

    def __repr__(self):
        return f'<Course {self.code}: {self.name}>'


class Enrollment(db.Model):
    __tablename__ = 'enrollments'

    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    course_id = db.Column(db.Integer, db.ForeignKey('courses.id'), nullable=False)
    enrolled_date = db.Column(db.DateTime, default=datetime.utcnow)

    __table_args__ = (db.UniqueConstraint('student_id', 'course_id', name='unique_enrollment'),)

    def __repr__(self):
        return f'<Enrollment student={self.student_id} course={self.course_id}>'


class Attendance(db.Model):
    __tablename__ = 'attendance'

    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    course_id = db.Column(db.Integer, db.ForeignKey('courses.id'), nullable=False)
    date = db.Column(db.Date, nullable=False)
    status = db.Column(db.String(10), nullable=False, default='absent')  # present/absent/late
    marked_at = db.Column(db.DateTime, default=datetime.utcnow)

    __table_args__ = (
        db.UniqueConstraint('student_id', 'course_id', 'date', name='unique_attendance'),
    )

    def __repr__(self):
        return f'<Attendance student={self.student_id} course={self.course_id} date={self.date} status={self.status}>'
