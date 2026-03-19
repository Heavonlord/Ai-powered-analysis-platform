import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders
from flask import current_app, render_template_string
from datetime import datetime


def send_email(to_email, subject, html_body, attachment_path=None):
    """Send an HTML email"""
    try:
        msg = MIMEMultipart('alternative')
        msg['Subject'] = subject
        msg['From'] = current_app.config['MAIL_DEFAULT_SENDER']
        msg['To'] = to_email

        msg.attach(MIMEText(html_body, 'html'))

        if attachment_path:
            with open(attachment_path, 'rb') as f:
                part = MIMEBase('application', 'octet-stream')
                part.set_payload(f.read())
                encoders.encode_base64(part)
                part.add_header('Content-Disposition',
                                f'attachment; filename="{attachment_path.split("/")[-1]}"')
                msg.attach(part)

        with smtplib.SMTP(current_app.config['MAIL_SERVER'],
                          current_app.config['MAIL_PORT']) as server:
            server.ehlo()
            if current_app.config['MAIL_USE_TLS']:
                server.starttls()
            if current_app.config['MAIL_USERNAME']:
                server.login(current_app.config['MAIL_USERNAME'],
                             current_app.config['MAIL_PASSWORD'])
            server.sendmail(msg['From'], to_email, msg.as_string())

        return True, "Email sent successfully"
    except Exception as e:
        current_app.logger.error(f"Email send error: {e}")
        return False, str(e)


def send_low_attendance_email(student, course, percentage):
    """Send low attendance alert email"""
    if not student.parent_email:
        return False, "No parent email"

    subject = f"⚠️ Low Attendance Alert - {student.username}"
    html = f"""
    <html><body style="font-family: Arial, sans-serif; max-width: 600px; margin: auto;">
    <div style="background: #1F3864; color: white; padding: 20px; border-radius: 8px 8px 0 0;">
        <h2>⚠️ Low Attendance Alert</h2>
    </div>
    <div style="border: 1px solid #ddd; padding: 20px; border-radius: 0 0 8px 8px;">
        <p>Dear Parent/Guardian,</p>
        <p>This is to inform you that <strong>{student.username}</strong> (Roll No: {student.roll_no or 'N/A'})
        has low attendance in the following course:</p>
        <table style="width:100%; border-collapse: collapse; margin: 15px 0;">
            <tr style="background:#f8f9fa">
                <td style="padding:10px; border:1px solid #ddd"><strong>Course</strong></td>
                <td style="padding:10px; border:1px solid #ddd">{course.name} ({course.code})</td>
            </tr>
            <tr>
                <td style="padding:10px; border:1px solid #ddd"><strong>Attendance</strong></td>
                <td style="padding:10px; border:1px solid #ddd; color:#dc3545"><strong>{percentage}%</strong></td>
            </tr>
        </table>
        <p style="color:#dc3545">⚠️ The minimum required attendance is <strong>75%</strong>.
        Please ensure your ward attends classes regularly.</p>
        <p>Please contact the teacher or institution for more information.</p>
        <hr>
        <small style="color:#666">AI Attendance Management System — {datetime.now().strftime('%d %b %Y')}</small>
    </div>
    </body></html>
    """
    return send_email(student.parent_email, subject, html)


def send_weekly_summary_email(student, course_stats):
    """Send weekly attendance summary email"""
    if not student.parent_email:
        return False, "No parent email"

    subject = f"📊 Weekly Attendance Report - {student.username}"
    rows = ""
    for cs in course_stats:
        color = "#28a745" if cs['pct'] >= 80 else "#ffc107" if cs['pct'] >= 75 else "#dc3545"
        rows += f"""<tr>
            <td style="padding:8px; border:1px solid #ddd">{cs['name']}</td>
            <td style="padding:8px; border:1px solid #ddd; color:{color}"><strong>{cs['pct']}%</strong></td>
            <td style="padding:8px; border:1px solid #ddd">{cs['present']}/{cs['total']}</td>
        </tr>"""

    html = f"""
    <html><body style="font-family: Arial, sans-serif; max-width: 600px; margin: auto;">
    <div style="background: #1F3864; color: white; padding: 20px; border-radius: 8px 8px 0 0;">
        <h2>📊 Weekly Attendance Summary</h2>
    </div>
    <div style="border: 1px solid #ddd; padding: 20px; border-radius: 0 0 8px 8px;">
        <p>Dear Parent/Guardian, here is <strong>{student.username}'s</strong> weekly attendance report:</p>
        <table style="width:100%; border-collapse: collapse; margin: 15px 0;">
            <tr style="background:#1F3864; color:white">
                <th style="padding:10px">Course</th>
                <th style="padding:10px">Attendance %</th>
                <th style="padding:10px">Classes</th>
            </tr>
            {rows}
        </table>
        <hr>
        <small style="color:#666">AI Attendance Management System — {datetime.now().strftime('%d %b %Y')}</small>
    </div>
    </body></html>
    """
    return send_email(student.parent_email, subject, html)
