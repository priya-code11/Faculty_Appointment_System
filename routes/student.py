import calendar
from datetime import date, datetime
from urllib.parse import quote_plus
from flask import (
    Blueprint,
    Response,
    abort,
    flash,
    redirect,
    render_template,
    request,
    url_for,
)
from flask_login import current_user, login_required
from models import db
from models.appointment import Appointment
from models.appointment_slot import AppointmentSlot
from models.faculty import Faculty
from models.student import Student
from utils.slot_generator import generate_slots_for_faculty

student = Blueprint(
    "student",
    __name__,
    url_prefix="/student"
)

# --------------------------------------------------
# HELPER FUNCTIONS
# --------------------------------------------------
def get_current_student():
    """Return the student profile of the logged-in user."""
    return Student.query.filter_by(
        user_id=current_user.id
    ).first()

def student_required():
    return (
        current_user.is_authenticated
        and current_user.role == "student"
    )

def get_active_booking_count(slot_id):
    """Count bookings that currently occupy slot capacity."""
    return Appointment.query.filter(
        Appointment.slot_id == slot_id,
        Appointment.status.in_(["pending", "accepted"])
    ).count()

def slot_is_in_the_future(slot):
    """Reject slots whose date/time has already passed."""
    now = datetime.now()
    slot_datetime = datetime.combine(
        slot.date,
        slot.period.start_time
    )
    return slot_datetime > now

def student_profile_or_404():
    """Return the logged-in student's profile or raise a 404."""
    student_profile = get_current_student()
    if not student_profile:
        abort(404, description="Student profile not found.")
    return student_profile

def generate_google_calendar_url(appointment):
    """Build a Google Calendar URL for a student's appointment."""
    slot = appointment.slot
    faculty = slot.faculty if slot else None
    if not slot or not faculty:
        raise ValueError("Appointment slot or faculty data is missing.")
    start_datetime = datetime.combine(
        slot.date,
        slot.period.start_time
    )
    end_datetime = datetime.combine(
        slot.date,
        slot.period.end_time
    )
    faculty_name = faculty.user.name if faculty.user else "Faculty"
    params = {
        "action": "TEMPLATE",
        "text": f"Appointment with {faculty_name}",
        "details": appointment.reason or "Faculty appointment",
        "location": getattr(faculty, "office_location", ""),
        "dates": (
            f"{start_datetime.strftime('%Y%m%dT%H%M%S')}"
            f"/{end_datetime.strftime('%Y%m%dT%H%M%S')}"
        ),
    }
    query_string = "&".join(
        f"{key}={quote_plus(str(value))}"
        for key, value in params.items()
    )
    return f"https://calendar.google.com/calendar/render?{query_string}"

def generate_ics_file(appointment):
    """Generate an ICS calendar file for a student appointment."""
    slot = appointment.slot
    faculty = slot.faculty if slot else None
    if not slot or not faculty:
        raise ValueError("Appointment slot or faculty data is missing.")
    start_datetime = datetime.combine(
        slot.date,
        slot.period.start_time
    )
    end_datetime = datetime.combine(
        slot.date,
        slot.period.end_time
    )
    faculty_name = faculty.user.name if faculty.user else "Faculty"
    return (
        "BEGIN:VCALENDAR\r\n"
        "VERSION:2.0\r\n"
        "PRODID:-//Faculty Appointment System//EN\r\n"
        "BEGIN:VEVENT\r\n"
        f"UID:{appointment.id}@faculty-appointment-system\r\n"
        f"DTSTAMP:{datetime.utcnow().strftime('%Y%m%dT%H%M%SZ')}\r\n"
        f"DTSTART:{start_datetime.strftime('%Y%m%dT%H%M%S')}\r\n"
        f"DTEND:{end_datetime.strftime('%Y%m%dT%H%M%S')}\r\n"
        f"SUMMARY:Appointment with {faculty_name}\r\n"
        f"DESCRIPTION:{appointment.reason or 'Faculty appointment'}\r\n"
        f"LOCATION:{getattr(faculty, 'office_location', '')}\r\n"
        "END:VEVENT\r\n"
        "END:VCALENDAR\r\n"
    )

# --------------------------------------------------
# STUDENT DASHBOARD
# --------------------------------------------------
@student.route("/dashboard")
@login_required
def dashboard():
    if not student_required():
        return "Unauthorized", 403
    student_profile = get_current_student()
    if not student_profile:
        return "Student profile not found.", 404
    appointments = Appointment.query.filter_by(
        student_id=student_profile.id
    ).all()
    upcoming_appointments = [
        appointment
        for appointment in appointments
        if appointment.status in ["pending", "accepted"]
        and slot_is_in_the_future(appointment.slot)
    ]
    return render_template(
        "student/dashboard.html",
        student=student_profile,
        user=current_user,
        appointments=appointments,
        upcoming_appointments=upcoming_appointments
    )

# --------------------------------------------------
# FACULTY LIST & AVAILABILITY ALIAS
# --------------------------------------------------
@student.route("/faculty")
@login_required
def faculty_list():
    if not student_required():
        return "Unauthorized", 403
    faculty_members = Faculty.query.all()
    for faculty_member in faculty_members:
        generate_slots_for_faculty(
            faculty_member.id,
            days=14
        )
    return render_template(
        "student/faculty_list.html",
        faculty_members=faculty_members
    )

@student.route("/availability/<string:faculty_id>")
@login_required
def faculty_availability(faculty_id):
    """Route alias matching templates/student/faculty_list.html"""
    return redirect(url_for("student.book_appointment", faculty_id=faculty_id))

# --------------------------------------------------
# VIEW AND BOOK APPOINTMENT
# --------------------------------------------------
@student.route(
    "/book/<string:faculty_id>",
    methods=["GET", "POST"]
)
@login_required
def book_appointment(faculty_id):
    if not student_required():
        return "Unauthorized", 403
    student_profile = get_current_student()
    if not student_profile:
        return "Student profile not found.", 404
    faculty_member = db.session.get(Faculty, faculty_id)
    if not faculty_member:
        flash("Faculty member not found.", "danger")
        return redirect(url_for("student.faculty_list"))

    # Ensure future slots exist
    generate_slots_for_faculty(faculty_member.id, days=14)

    if request.method == "POST":
        reason = request.form.get("reason", "").strip()
        slot_id = request.form.get("slot_id")

        if not reason:
            flash("Please enter the reason for your appointment.", "danger")
            return redirect(url_for("student.book_appointment", faculty_id=faculty_id))

        if not slot_id:
            flash("Please select an appointment slot.", "danger")
            return redirect(url_for("student.book_appointment", faculty_id=faculty_id))

        slot = AppointmentSlot.query.filter_by(
            id=slot_id,
            faculty_id=faculty_member.id
        ).first()

        if not slot:
            flash("Invalid appointment slot.", "danger")
            return redirect(url_for("student.book_appointment", faculty_id=faculty_id))

        if not faculty_member.is_available:
            flash("This faculty member is currently Busy.", "warning")
            return redirect(url_for("student.book_appointment", faculty_id=faculty_id))

        if not slot_is_in_the_future(slot):
            flash("This appointment time has already passed.", "danger")
            return redirect(url_for("student.book_appointment", faculty_id=faculty_id))

        existing_booking = Appointment.query.filter(
            Appointment.student_id == student_profile.id,
            Appointment.slot_id == slot.id,
            Appointment.status.in_(["pending", "accepted"])
        ).first()

        if existing_booking:
            flash("You have already booked this appointment slot.", "warning")
            return redirect(url_for("student.appointments"))

        booked_count = get_active_booking_count(slot.id)
        if booked_count >= slot.capacity:
            flash("Sorry, this appointment slot is Full.", "warning")
            return redirect(url_for("student.book_appointment", faculty_id=faculty_id))

        appointment = Appointment(
            student_id=student_profile.id,
            slot_id=slot.id,
            reason=reason,
            status="pending"
        )
        db.session.add(appointment)
        db.session.commit()
        flash("Appointment booked successfully!", "success")
        return redirect(url_for("student.appointments"))

    today = date.today()

    slots = AppointmentSlot.query.filter_by(
        faculty_id=faculty_member.id
    ).filter(
        AppointmentSlot.date >= today
    ).order_by(
        AppointmentSlot.date
    ).all()

    slots = [slot for slot in slots if slot_is_in_the_future(slot)]
    slots.sort(key=lambda s: (s.date, s.period.start_time))

    slots_by_date = {}
    for slot in slots:
        date_key = slot.date.isoformat()
        slots_by_date.setdefault(date_key, []).append(slot)

    cal = calendar.Calendar(firstweekday=6)
    month_days = cal.monthdatescalendar(today.year, today.month)
    max_bookable_date = today.fromordinal(today.toordinal() + 14)

    return render_template(
        "student/book_appointment.html",
        faculty=faculty_member,
        slots=slots,
        slots_by_date=slots_by_date,
        month_days=month_days,
        today=today,
        today_str=today.isoformat(),
        max_bookable_date=max_bookable_date
    )

# --------------------------------------------------
# MY APPOINTMENTS
# --------------------------------------------------
@student.route("/appointments")
@login_required
def appointments():
    if not student_required():
        return "Unauthorized", 403
    student_profile = get_current_student()
    if not student_profile:
        return "Student profile not found.", 404
    appointments_list = Appointment.query.filter_by(
        student_id=student_profile.id
    ).all()
    appointments_list.sort(
        key=lambda appointment: (
            appointment.slot.date,
            appointment.slot.period.start_time
        ),
        reverse=True
    )
    return render_template(
        "student/appointments.html",
        appointments=appointments_list,
        current_date=datetime.now()
    )

# --------------------------------------------------
# CANCEL APPOINTMENT
# --------------------------------------------------
@student.route("/appointments/cancel/<string:appointment_id>", methods=["POST"])
@login_required
def cancel_appointment(appointment_id):
    if not student_required():
        return "Unauthorized", 403
    student_profile = get_current_student()
    if not student_profile:
        return "Student profile not found.", 404

    appointment = Appointment.query.filter_by(
        id=appointment_id,
        student_id=student_profile.id
    ).first()

    if not appointment:
        flash("Appointment not found.", "danger")
        return redirect(url_for("student.appointments"))

    if appointment.status not in ["pending", "accepted"]:
        flash("This appointment can no longer be cancelled.", "warning")
        return redirect(url_for("student.appointments"))

    if not slot_is_in_the_future(appointment.slot):
        flash("A past appointment cannot be cancelled.", "warning")
        return redirect(url_for("student.appointments"))

    appointment.status = "cancelled"
    db.session.commit()
    flash("Appointment cancelled successfully. The slot is available again.", "success")
    return redirect(url_for("student.appointments"))

# --------------------------------------------------
# CALENDAR EXPORTS
# --------------------------------------------------
@student.route("/appointments/<string:appointment_id>/calendar", methods=["GET"])
@login_required
def appointment_google_calendar(appointment_id):
    student_profile = student_profile_or_404()
    appointment = Appointment.query.filter_by(
        id=appointment_id,
        student_id=student_profile.id
    ).first()
    if not appointment:
        flash("Appointment not found.", "danger")
        return redirect(url_for("student.appointments"))
    if appointment.status not in ["pending", "accepted"]:
        flash("This appointment cannot be exported to Google Calendar.", "warning")
        return redirect(url_for("student.appointments"))
    return redirect(generate_google_calendar_url(appointment))

@student.route("/appointments/<string:appointment_id>/ics", methods=["GET"])
@login_required
def appointment_ics(appointment_id):
    student_profile = student_profile_or_404()
    appointment = Appointment.query.filter_by(
        id=appointment_id,
        student_id=student_profile.id
    ).first()
    if not appointment:
        flash("Appointment not found.", "danger")
        return redirect(url_for("student.appointments"))
    ics_file = generate_ics_file(appointment)
    return Response(
        ics_file,
        mimetype="text/calendar",
        headers={
            "Content-Disposition": (
                f"attachment; filename=appointment-{appointment.id}.ics"
            )
        }
    )