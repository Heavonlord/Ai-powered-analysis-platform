"""
Predictive Analytics Engine for AttendAI
Uses scikit-learn to predict attendance trends and risk trajectories.
Falls back to rule-based predictions if sklearn is not installed.
"""
from datetime import date, timedelta
from collections import defaultdict


def get_attendance_trend(student_id, course_id, db, Attendance):
    """
    Returns a list of (date, cumulative_percentage) tuples
    representing the student's attendance trajectory over time.
    """
    records = (
        Attendance.query
        .filter_by(student_id=student_id, course_id=course_id)
        .order_by(Attendance.date)
        .all()
    )
    if not records:
        return []

    trend = []
    present_count = 0
    for i, r in enumerate(records, 1):
        if r.status in ('present', 'late'):
            present_count += 1
        pct = round((present_count / i) * 100, 1)
        trend.append({'date': r.date.isoformat(), 'pct': pct, 'status': r.status})
    return trend


def predict_future_attendance(student_id, course_id, db, Attendance, future_classes=10):
    """
    Predicts attendance percentage after N future classes.
    Uses linear regression if sklearn available, else moving average.
    Returns dict with prediction, confidence, and recommendation.
    """
    records = (
        Attendance.query
        .filter_by(student_id=student_id, course_id=course_id)
        .order_by(Attendance.date)
        .all()
    )
    if len(records) < 3:
        return None

    total = len(records)
    present = sum(1 for r in records if r.status in ('present', 'late'))
    current_pct = (present / total) * 100

    try:
        from sklearn.linear_model import LinearRegression
        import numpy as np

        # Build cumulative percentage series
        cumulative = []
        p = 0
        for i, r in enumerate(records, 1):
            if r.status in ('present', 'late'):
                p += 1
            cumulative.append(p / i * 100)

        X = np.array(range(len(cumulative))).reshape(-1, 1)
        y = np.array(cumulative)
        model = LinearRegression().fit(X, y)

        future_x = np.array([total + future_classes]).reshape(-1, 1)
        predicted_pct = float(model.predict(future_x)[0])
        predicted_pct = max(0, min(100, predicted_pct))

        # Confidence based on R²
        r2 = model.score(X, y)
        confidence = 'high' if r2 > 0.7 else 'medium' if r2 > 0.4 else 'low'

        method = 'linear_regression'

    except ImportError:
        # Fallback: weighted moving average (recent classes matter more)
        recent = records[-min(10, len(records)):]
        recent_present = sum(1 for r in recent if r.status in ('present', 'late'))
        recent_pct = (recent_present / len(recent)) * 100

        # Blend current overall with recent trend
        predicted_pct = 0.4 * current_pct + 0.6 * recent_pct
        confidence = 'medium'
        method = 'weighted_average'

    # Generate recommendation
    if predicted_pct >= 80:
        recommendation = "On track — excellent attendance trend."
        rec_color = "success"
    elif predicted_pct >= 75:
        recommendation = "Borderline — attend all remaining classes to stay safe."
        rec_color = "warning"
    elif predicted_pct >= 65:
        recommendation = "At risk — must attend at least 90% of remaining classes."
        rec_color = "orange"
    else:
        recommendation = "Critical trajectory — immediate intervention required."
        rec_color = "danger"

    return {
        'current_pct': round(current_pct, 1),
        'predicted_pct': round(predicted_pct, 1),
        'future_classes': future_classes,
        'confidence': confidence,
        'recommendation': recommendation,
        'rec_color': rec_color,
        'method': method,
    }


def get_weekly_pattern(student_id, course_id, db, Attendance):
    """
    Analyse which days of the week a student is most likely to be absent.
    Returns a dict: {'Monday': 85.0, 'Tuesday': 92.0, ...}
    """
    day_names = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
    day_stats = defaultdict(lambda: {'present': 0, 'total': 0})

    records = Attendance.query.filter_by(student_id=student_id, course_id=course_id).all()
    for r in records:
        d = r.date.weekday()
        day_stats[d]['total'] += 1
        if r.status in ('present', 'late'):
            day_stats[d]['present'] += 1

    result = {}
    for d, stats in day_stats.items():
        if stats['total'] > 0:
            result[day_names[d]] = round((stats['present'] / stats['total']) * 100, 1)
    return result


def get_course_heatmap(course_id, db, Attendance, User, Enrollment):
    """
    Returns a 2D heatmap: students × dates with status values.
    Useful for Chart.js or Plotly heatmap visualizations.
    """
    enrolled_ids = [
        e.student_id for e in
        Enrollment.query.filter_by(course_id=course_id).all()
    ]
    students = User.query.filter(User.id.in_(enrolled_ids)).order_by(User.roll_no).all()

    # Get all distinct dates for this course
    from sqlalchemy import distinct
    dates = sorted(set(
        r.date for r in Attendance.query.filter_by(course_id=course_id).all()
    ))

    # Build matrix
    att_map = {
        (r.student_id, r.date): r.status
        for r in Attendance.query.filter_by(course_id=course_id).all()
    }

    heatmap = []
    for s in students:
        row = {
            'student': s.username,
            'roll_no': s.roll_no or 'N/A',
            'data': [att_map.get((s.id, d), 'no_class') for d in dates]
        }
        heatmap.append(row)

    return {
        'students': [s.username for s in students],
        'dates': [d.isoformat() for d in dates],
        'heatmap': heatmap,
    }


def classify_risk_batch(students, course_id=None):
    """
    Classify a list of students by risk level in one pass.
    Returns dict: {risk_level: [student_list]}
    """
    buckets = {'SAFE': [], 'CAUTION': [], 'WARNING': [], 'CRITICAL': []}
    for s in students:
        pct = s.get_attendance_percentage(course_id)
        risk, _ = s.get_risk_level(course_id)
        buckets[risk].append({'student': s, 'pct': pct})
    return buckets
