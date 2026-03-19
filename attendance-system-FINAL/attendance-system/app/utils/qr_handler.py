import qrcode
import jwt
import io
import base64
from datetime import datetime, timedelta
from flask import current_app


def generate_qr_token(course_id, teacher_id, expiry_minutes=5):
    """Generate a JWT token for QR code attendance"""
    payload = {
        'course_id': course_id,
        'teacher_id': teacher_id,
        'exp': datetime.utcnow() + timedelta(minutes=expiry_minutes),
        'iat': datetime.utcnow(),
        'type': 'attendance_qr'
    }
    token = jwt.encode(payload, current_app.config['JWT_SECRET'], algorithm='HS256')
    return token


def validate_qr_token(token):
    """Validate JWT token from QR code scan"""
    try:
        payload = jwt.decode(token, current_app.config['JWT_SECRET'], algorithms=['HS256'])
        if payload.get('type') != 'attendance_qr':
            return None, 'Invalid token type'
        return payload, None
    except jwt.ExpiredSignatureError:
        return None, 'QR code has expired. Please ask teacher to generate a new one.'
    except jwt.InvalidTokenError:
        return None, 'Invalid QR code.'


def generate_qr_image(token, course_name):
    """Generate a QR code image as base64 string"""
    # Create QR code
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_L,
        box_size=10,
        border=4,
    )

    # The URL students scan (in real deployment, replace with actual domain)
    scan_url = f"ATTENDANCE:{token}"
    qr.add_data(scan_url)
    qr.make(fit=True)

    img = qr.make_image(fill_color="#1F3864", back_color="white")

    # Convert to base64
    buffer = io.BytesIO()
    img.save(buffer, format='PNG')
    buffer.seek(0)
    img_base64 = base64.b64encode(buffer.getvalue()).decode('utf-8')

    return img_base64
