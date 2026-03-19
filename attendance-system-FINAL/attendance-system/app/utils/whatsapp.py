from flask import current_app
from datetime import datetime


def send_whatsapp_message(to_number, message):
    """Send a WhatsApp message via Twilio"""
    try:
        from twilio.rest import Client
        client = Client(
            current_app.config['TWILIO_ACCOUNT_SID'],
            current_app.config['TWILIO_AUTH_TOKEN']
        )
        msg = client.messages.create(
            body=message,
            from_=current_app.config['TWILIO_WHATSAPP_FROM'],
            to=f'whatsapp:{to_number}'
        )
        return True, msg.sid
    except ImportError:
        current_app.logger.warning("Twilio not installed. WhatsApp notifications disabled.")
        return False, "Twilio not installed"
    except Exception as e:
        current_app.logger.error(f"WhatsApp send error: {e}")
        return False, str(e)


def send_low_attendance_alert(student, course, percentage):
    """Send low attendance alert to parent"""
    if not student.parent_phone:
        return False, "No parent phone number"

    message = f"""🚨 Low Attendance Alert
Student: {student.username}
Roll No: {student.roll_no or 'N/A'}
Course: {course.name} ({course.code})
Current Attendance: {percentage}%
⚠️ Attendance is below 80%. Please ensure regular attendance.

AI Attendance System
{datetime.now().strftime('%d %b %Y, %I:%M %p')}"""

    return send_whatsapp_message(student.parent_phone, message)


def send_critical_alert(student, course, percentage, classes_needed):
    """Send critical attendance alert to parent"""
    if not student.parent_phone:
        return False, "No parent phone number"

    message = f"""🚨 CRITICAL ATTENDANCE ALERT 🚨
Student: {student.username}
Roll No: {student.roll_no or 'N/A'}
Course: {course.name} ({course.code})
Current Attendance: {percentage}%
⚠️ URGENT: Attendance is below 65%!
Student needs {classes_needed} continuous present marks to recover.
IMMEDIATE ACTION REQUIRED!
Please contact the teacher.

AI Attendance System
{datetime.now().strftime('%d %b %Y, %I:%M %p')}"""

    return send_whatsapp_message(student.parent_phone, message)


def send_daily_summary(student, course_data):
    """Send daily attendance summary to parent"""
    if not student.parent_phone:
        return False, "No parent phone number"

    course_lines = "\n".join([f"  {c['name']}: {c['percentage']}%" for c in course_data])
    overall = sum(c['percentage'] for c in course_data) / len(course_data) if course_data else 0

    message = f"""📊 Daily Attendance Summary
Student: {student.username}
Date: {datetime.now().strftime('%d %b %Y')}
Overall Attendance: {overall:.1f}%
Course-wise:
{course_lines}

AI Attendance System"""

    return send_whatsapp_message(student.parent_phone, message)
