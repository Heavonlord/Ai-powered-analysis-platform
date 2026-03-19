"""
Scheduled background tasks for AttendAI.
Uses APScheduler — install with: pip install APScheduler
"""
import logging
from datetime import datetime, date, timedelta

logger = logging.getLogger(__name__)


def init_scheduler(app):
    """Initialize and start the background task scheduler."""
    try:
        from apscheduler.schedulers.background import BackgroundScheduler
        from apscheduler.triggers.cron import CronTrigger
    except ImportError:
        logger.warning("APScheduler not installed. Scheduled tasks disabled. Run: pip install APScheduler")
        return None

    scheduler = BackgroundScheduler(timezone='Asia/Kolkata')

    # Daily: 6 PM — send daily summaries to parents
    scheduler.add_job(
        func=lambda: run_with_context(app, daily_parent_summaries),
        trigger=CronTrigger(hour=18, minute=0),
        id='daily_summaries',
        name='Daily Parent Summaries',
        replace_existing=True
    )

    # Daily: 7 PM — alert parents of low-attendance students
    scheduler.add_job(
        func=lambda: run_with_context(app, daily_low_attendance_alerts),
        trigger=CronTrigger(hour=19, minute=0),
        id='low_attendance_alerts',
        name='Low Attendance Alerts',
        replace_existing=True
    )

    # Weekly: Friday 5 PM — weekly summaries
    scheduler.add_job(
        func=lambda: run_with_context(app, weekly_summaries),
        trigger=CronTrigger(day_of_week='fri', hour=17, minute=0),
        id='weekly_summaries',
        name='Weekly Summaries',
        replace_existing=True
    )

    scheduler.start()
    logger.info("✅ Scheduler started with %d jobs", len(scheduler.get_jobs()))
    return scheduler


def run_with_context(app, func):
    """Run a task function within Flask app context."""
    with app.app_context():
        try:
            func()
        except Exception as e:
            logger.error("Scheduled task %s failed: %s", func.__name__, str(e))


def daily_parent_summaries():
    """Send daily attendance summary to all parents."""
    from app.models import User, Course, Attendance, Enrollment
    from app.utils.whatsapp import send_daily_summary
    from app.utils.email_handler import send_weekly_summary_email

    students = User.query.filter_by(role='student', is_active=True).all()
    today = date.today()
    sent = 0

    for student in students:
        if not (student.parent_phone or student.parent_email):
            continue

        enrollments = Enrollment.query.filter_by(student_id=student.id).all()
        course_data = []
        for e in enrollments:
            course = Course.query.get(e.course_id)
            if course:
                pct = student.get_attendance_percentage(course.id)
                course_data.append({
                    'name': course.code,
                    'percentage': pct,
                    'present': Attendance.query.filter_by(
                        student_id=student.id, course_id=course.id
                    ).filter(Attendance.status.in_(['present', 'late'])).count(),
                    'total': Attendance.query.filter_by(
                        student_id=student.id, course_id=course.id
                    ).count(),
                    'pct': pct
                })

        if not course_data:
            continue

        if student.parent_phone:
            try:
                send_daily_summary(student, course_data)
                sent += 1
            except Exception as e:
                logger.error("WhatsApp daily summary failed for %s: %s", student.username, e)

    logger.info("Daily summaries sent: %d", sent)


def daily_low_attendance_alerts():
    """Alert parents of students with attendance below 80%."""
    from app.models import User, Course, Enrollment
    from app.utils.whatsapp import send_low_attendance_alert, send_critical_alert
    from app.utils.email_handler import send_low_attendance_email

    students = User.query.filter_by(role='student', is_active=True).all()
    alerted = 0

    for student in students:
        enrollments = Enrollment.query.filter_by(student_id=student.id).all()
        for e in enrollments:
            course = Course.query.get(e.course_id)
            if not course:
                continue
            pct = student.get_attendance_percentage(course.id)
            if pct >= 80:
                continue

            _, classes_needed = student.get_can_miss(course.id)

            if student.parent_phone:
                try:
                    if pct < 65:
                        send_critical_alert(student, course, pct, classes_needed)
                    else:
                        send_low_attendance_alert(student, course, pct)
                    alerted += 1
                except Exception as ex:
                    logger.error("Alert failed for %s/%s: %s", student.username, course.code, ex)

    logger.info("Low attendance alerts sent: %d", alerted)


def weekly_summaries():
    """Send weekly attendance email summaries to parents."""
    from app.models import User, Course, Enrollment, Attendance
    from app.utils.email_handler import send_weekly_summary_email

    students = User.query.filter_by(role='student', is_active=True).all()
    sent = 0

    for student in students:
        if not student.parent_email:
            continue
        enrollments = Enrollment.query.filter_by(student_id=student.id).all()
        course_stats = []
        for e in enrollments:
            course = Course.query.get(e.course_id)
            if course:
                pct = student.get_attendance_percentage(course.id)
                present = Attendance.query.filter_by(
                    student_id=student.id, course_id=course.id
                ).filter(Attendance.status.in_(['present', 'late'])).count()
                total = Attendance.query.filter_by(
                    student_id=student.id, course_id=course.id
                ).count()
                course_stats.append({'name': course.name, 'pct': pct, 'present': present, 'total': total})

        if course_stats:
            try:
                send_weekly_summary_email(student, course_stats)
                sent += 1
            except Exception as ex:
                logger.error("Weekly summary email failed for %s: %s", student.username, ex)

    logger.info("Weekly summaries sent: %d", sent)
