# AttendAI — AI-Powered Student Attendance Management System

> A production-ready Flask application with predictive analytics, real-time WebSockets, QR code attendance, voice recognition, and WhatsApp/email notifications.

---

## 📋 Table of Contents
- [Features](#features)
- [Technology Stack](#technology-stack)
- [Quick Start](#quick-start)
- [Project Structure](#project-structure)
- [Usage Guide](#usage-guide)
- [API Reference](#api-reference)
- [Deployment](#deployment)
- [Demo Accounts](#demo-accounts)

---

## ✨ Features

### Core
| Feature | Description |
|---------|-------------|
| 🔐 Role-Based Auth | Admin / Teacher / Student with Bcrypt + session management |
| 📝 Manual Attendance | Present/Absent/Late with date selector and bulk mark |
| ⌨️ Keyboard Shortcuts | P/A/L keys + ↑↓ navigation + Ctrl+Enter submit |
| 🎙️ Voice Recognition | Web Speech API — "Roll 101 present, Roll 102 absent" |
| 📱 QR Code | 5-minute JWT tokens, camera scanner, real-time list |
| 📊 Predictive Analytics | Risk levels, "can miss X" calculator, progress bars |
| ⚡ Real-Time Dashboard | WebSocket (Socket.IO) live attendance updates |
| 📲 WhatsApp Alerts | Twilio integration — parent notifications |
| 📧 Email Notifications | SMTP HTML emails to parents |
| 📊 Excel Export | Color-coded openpyxl reports |
| 📤 CSV Bulk Upload | Add 1000 students at once |
| 📱 PWA Support | Installable mobile app for students |

### Analytics Engine
- **SAFE** (≥80%) — Green
- **CAUTION** (75–79%) — Yellow  
- **WARNING** (65–74%) — Orange
- **CRITICAL** (<65%) — Red
- "Can miss X more classes" calculator
- "Need Y classes to reach 75%" for at-risk students

---

## 🛠 Technology Stack

- **Backend**: Python 3.12, Flask 3.0
- **Database**: SQLite (dev) / PostgreSQL (prod)
- **ORM**: SQLAlchemy + Flask-SQLAlchemy
- **Auth**: Flask-Login + Bcrypt
- **WebSockets**: Flask-SocketIO + eventlet
- **Frontend**: Bootstrap 5, jQuery, Chart.js
- **QR**: qrcode + PyJWT
- **Reports**: openpyxl
- **Notifications**: Twilio (WhatsApp) + smtplib (Email)

---

## 🚀 Quick Start

### Option 1: Auto Setup (Recommended)
```bash
git clone <repo-url>
cd attendance-system
chmod +x INSTALL.sh
./INSTALL.sh
```

### Option 2: Manual Setup
```bash
# 1. Clone & enter directory
git clone <repo-url> && cd attendance-system

# 2. Create virtual environment
python3 -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Configure environment
cp .env.example .env
# Edit .env with your credentials

# 5. Setup database + sample data
python create_admin.py --seed

# 6. Run
python run.py
```

Open **http://localhost:5000** in your browser.

---

## 📁 Project Structure

```
attendance-system/
├── run.py                     # App entry point
├── config.py                  # Dev/Prod config classes
├── create_admin.py            # DB init + sample data seeder
├── requirements.txt
├── Procfile                   # gunicorn (production)
├── INSTALL.sh                 # One-command setup
├── .env.example               # Environment variable template
├── app/
│   ├── __init__.py            # Flask app factory
│   ├── models.py              # User, Course, Enrollment, Attendance
│   ├── routes.py              # All route handlers
│   ├── utils/
│   │   ├── qr_handler.py      # QR code + JWT generation
│   │   ├── whatsapp.py        # Twilio WhatsApp integration
│   │   └── email_handler.py   # SMTP email notifications
│   ├── static/
│   │   ├── css/custom.css     # Design system
│   │   ├── js/app.js          # WebSocket + UI helpers
│   │   └── sw.js              # PWA service worker
│   └── templates/
│       ├── base.html
│       ├── index.html
│       ├── login.html
│       ├── admin_dashboard.html
│       ├── admin_analytics.html
│       ├── teacher_dashboard.html
│       ├── manage_enrollments.html
│       ├── mark_attendance.html   # Manual + Voice + Keyboard
│       ├── qr_display.html
│       ├── scan_qr.html
│       ├── course_analytics.html
│       └── student_dashboard.html
└── instance/
    └── attendance.db          # SQLite database
```

---

## 📖 Usage Guide

### Admin
1. Login → Admin Dashboard
2. **Add users**: Click "Add User" or bulk upload via CSV
3. **Add courses**: Click "Add Course", assign to a teacher
4. **Analytics**: View system-wide risk distribution

### Teacher
1. Login → Teacher Dashboard (see assigned courses)
2. **Mark Attendance**:
   - **Manual**: Click P/A/L buttons for each student
   - **Keyboard**: Press P, A, or L keys (auto-advances)
   - **Voice**: Click mic, say "Roll 101 present, Roll 102 absent"
   - **QR Code**: Generate QR, students scan with phone
3. **Analytics**: View predictive risk levels, export Excel
4. **Alerts**: Click 🔔 to notify a parent via WhatsApp/Email
5. **Enrollments**: Add/remove students from courses

### Student
1. Login → Student Dashboard
2. View overall % and per-course breakdown
3. See risk level and "can miss X classes" indicator
4. **Scan QR**: Click "Scan QR" → allow camera → scan teacher's QR

---

## 🔌 API Reference

| Method | Endpoint | Auth | Description |
|--------|----------|------|-------------|
| POST | `/api/qr/scan` | Student | Mark attendance via QR token |
| GET | `/api/analytics/overview` | Admin | System analytics JSON |

### WebSocket Events
| Event | Direction | Payload |
|-------|-----------|---------|
| `join_course` | Client→Server | `{course_id}` |
| `student_scanned` | Server→Client | `{student_name, roll_no, time}` |
| `attendance_updated` | Server→Client | `{course_id, date, count}` |

---

## 🚀 Deployment

### Render.com (Free)
```bash
# 1. Push to GitHub
git init && git add . && git commit -m "initial"
git remote add origin <your-repo>
git push

# 2. Connect to Render.com
# - New Web Service → connect repo
# - Build command: pip install -r requirements.txt && python create_admin.py
# - Start command: gunicorn --worker-class eventlet -w 1 run:app
# - Add environment variables from .env.example
```

### Environment Variables (Production)
```
SECRET_KEY=<random-64-char-string>
DATABASE_URL=<postgresql-url>
TWILIO_ACCOUNT_SID=<your-sid>
TWILIO_AUTH_TOKEN=<your-token>
MAIL_USERNAME=<gmail>
MAIL_PASSWORD=<app-password>
```

---

## 🔑 Demo Accounts

| Role | Username | Password |
|------|----------|----------|
| Admin | `admin` | `admin123` |
| Teacher | `teacher1` | `teacher123` |
| Teacher | `teacher2` | `teacher123` |
| Student | `student1`–`student20` | `student123` |

> Sample data includes 30 days of realistic attendance with varied risk levels.

---

## 🔒 Security Features
- Bcrypt password hashing (12 rounds)
- Account lockout after 5 failed logins (30 min)
- JWT tokens for QR codes (5-min expiry)
- Role-based access on every route
- SQLAlchemy ORM (SQL injection prevention)
- Jinja2 auto-escaping (XSS prevention)

---

## 📄 License
MIT License — Free for academic use.
