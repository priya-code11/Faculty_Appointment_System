from flask import (
    Blueprint,
    render_template,
    request,
    redirect,
    url_for,
    flash
)
from datetime import date, datetime
from sqlalchemy.orm import joinedload
from flask_login import login_required, current_user
from models import db
from models.faculty import Faculty
from models.faculty_timetable import FacultyTimetable
from models.schedule_period import SchedulePeriod
from models.appointment_slot import AppointmentSlot
from models.appointment import Appointment
from utils.slot_generator import generate_slots_for_faculty

faculty = Blueprint(
    "faculty",
    __name__,
    url_prefix="/faculty"
)

def faculty_required():
    return (
        current_user.is_authenticated
        and current_user.role == "faculty"
    )

@faculty.route("/dashboard")
@login_required
def dashboard():
    if not faculty_required():
        return "Unauthorized", 403

    faculty_member = Faculty.query.filter_by(user_id=current_user.id).first()
    if not faculty_member:
        flash("Faculty profile not found.", "danger")
        return redirect(url_for("auth.login"))

    # Generate slots for upcoming 14 days automatically
    generate_slots_for_faculty(faculty_member.id, days=14)

    today = date.today()
    now_time = datetime.now().time()
    today_weekday = today.weekday()  # Monday = 0 ... Sunday = 6

    # 1. Today's Lectures from the Timetable (ordered by period start time)
    today_lectures = (
        FacultyTimetable.query.options(joinedload(FacultyTimetable.period))
        .filter_by(faculty_id=faculty_member.id, day_of_week=today_weekday)
        .join(SchedulePeriod)
        .order_by(SchedulePeriod.start_time.asc())
        .all()
    )

    # 2. Upcoming Student Appointments (Starting today onwards)
    all_upcoming_appointments = (
        Appointment.query.options(
            joinedload(Appointment.student),
            joinedload(Appointment.slot).joinedload(AppointmentSlot.period),
        )
        .join(AppointmentSlot)
        .filter(
            AppointmentSlot.faculty_id == faculty_member.id,
            AppointmentSlot.date >= today,
            Appointment.status.in_(["pending", "accepted"])
        )
        .order_by(AppointmentSlot.date.asc())
        .all()
    )

    # Filter out appointments whose time has already passed today
    upcoming_appointments = [
        appt for appt in all_upcoming_appointments
        if appt.slot.date > today or (appt.slot.date == today and appt.slot.period.end_time > now_time)
    ]
    # Sort by slot date and start time
    upcoming_appointments.sort(key=lambda a: (a.slot.date, a.slot.period.start_time))

    # 3. Today's appointments specifically (for quick count/display)
    today_appointments = [
        appt for appt in upcoming_appointments
        if appt.slot.date == today
    ]

    return render_template(
        "faculty/dashboard.html",
        faculty=faculty_member,
        today_lectures=today_lectures,
        upcoming_appointments=upcoming_appointments,
        today_appointments=today_appointments,
        today=today,
        days_names=["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
    )

@faculty.route("/timetable")
@login_required
def timetable():
    if not faculty_required():
        return "Unauthorized", 403
    faculty_member = Faculty.query.filter_by(
        user_id=current_user.id
    ).first()
    periods = SchedulePeriod.query.order_by(
        SchedulePeriod.order
    ).all()
    timetable_entries = FacultyTimetable.query.filter_by(
        faculty_id=faculty_member.id
    ).all()
    timetable_map = {}
    for entry in timetable_entries:
        timetable_map[
            (entry.day_of_week, entry.period_id)
        ] = entry
    days = [
        (0, "Monday"),
        (1, "Tuesday"),
        (2, "Wednesday"),
        (3, "Thursday"),
        (4, "Friday"),
        (5, "Saturday")
    ]
    return render_template(
        "faculty/timetable.html",
        faculty=faculty_member,
        periods=periods,
        days=days,
        timetable_map=timetable_map
    )

@faculty.route("/timetable/add", methods=["POST"])
@login_required
def add_timetable():
    if not faculty_required():
        return "Unauthorized", 403
    faculty_member = Faculty.query.filter_by(
        user_id=current_user.id
    ).first()
    day_of_week = request.form.get("day_of_week")
    period_id = request.form.get("period_id")
    subject = request.form.get("subject", "").strip()

    if not day_of_week or not period_id:
        flash("Please select a day and period.", "danger")
        return redirect(url_for("faculty.timetable"))

    try:
        day_of_week = int(day_of_week)
    except ValueError:
        flash("Invalid day selected.", "danger")
        return redirect(url_for("faculty.timetable"))

    period = db.session.get(SchedulePeriod, period_id)
    if not period:
        flash("Invalid period selected.", "danger")
        return redirect(url_for("faculty.timetable"))

    existing_entry = FacultyTimetable.query.filter_by(
        faculty_id=faculty_member.id,
        day_of_week=day_of_week,
        period_id=period_id
    ).first()
    if existing_entry:
        flash("This period already has a lecture.", "warning")
        return redirect(url_for("faculty.timetable"))

    if not subject:
        flash("Please enter the subject name.", "danger")
        return redirect(url_for("faculty.timetable"))

    entry = FacultyTimetable(
        faculty_id=faculty_member.id,
        period_id=period_id,
        day_of_week=day_of_week,
        subject=subject
    )
    db.session.add(entry)
    db.session.commit()
    flash("Lecture added to timetable.", "success")
    return redirect(url_for("faculty.timetable"))

@faculty.route("/timetable/delete/<string:entry_id>", methods=["POST"])
@login_required
def delete_timetable(entry_id):
    if not faculty_required():
        return "Unauthorized", 403
    faculty_member = Faculty.query.filter_by(
        user_id=current_user.id
    ).first()
    entry = FacultyTimetable.query.filter_by(
        id=entry_id,
        faculty_id=faculty_member.id
    ).first()
    if not entry:
        flash("Timetable entry not found.", "danger")
        return redirect(url_for("faculty.timetable"))

    db.session.delete(entry)
    db.session.commit()
    flash("Lecture removed from timetable.", "success")
    return redirect(url_for("faculty.timetable"))

@faculty.route("/availability/toggle", methods=["POST"])
@login_required
def toggle_availability():
    if not faculty_required():
        return "Unauthorized", 403
    faculty_member = Faculty.query.filter_by(
        user_id=current_user.id
    ).first()
    faculty_member.is_available = not faculty_member.is_available
    db.session.commit()
    if faculty_member.is_available:
        flash("You are now Available for appointments.", "success")
    else:
        flash("You are now Busy. Students cannot book appointments.", "warning")
    return redirect(url_for("faculty.dashboard"))

@faculty.route("/appointment-slots")
@login_required
def appointment_slots():
    if not faculty_required():
        return "Unauthorized", 403

    faculty_member = Faculty.query.filter_by(
        user_id=current_user.id
    ).first()

    if not faculty_member:
        flash("Faculty profile not found.", "danger")
        return redirect(url_for("auth.login"))

    # Regenerate & clean up timetable conflicts
    generate_slots_for_faculty(faculty_member.id, days=14)

    today = date.today()
    all_slots = (
        AppointmentSlot.query.filter(
            AppointmentSlot.faculty_id == faculty_member.id,
            AppointmentSlot.date >= today
        )
        .order_by(AppointmentSlot.date.asc(), AppointmentSlot.period_id.asc())
        .all()
    )

    # Filter to ONLY free slots (capacity available)
    free_slots = [slot for slot in all_slots if not slot.is_full]

    return render_template(
        "faculty/slots.html",
        faculty=faculty_member,
        slots=free_slots,
        today=today
    )

@faculty.route("/appointments")
@login_required
def appointments():
    if not faculty_required():
        return "Unauthorized", 403
    faculty_member = Faculty.query.filter_by(
        user_id=current_user.id
    ).first()
    appointments = (
        Appointment.query.join(AppointmentSlot)
        .filter(AppointmentSlot.faculty_id == faculty_member.id)
        .order_by(AppointmentSlot.date.desc())
        .all()
    )
    return render_template(
        "faculty/appointments.html",
        appointments=appointments
    )

@faculty.route("/appointments/<string:appointment_id>/<string:action>", methods=["POST"])
@login_required
def update_appointment(appointment_id, action):
    if not faculty_required():
        return "Unauthorized", 403
    faculty_member = Faculty.query.filter_by(
        user_id=current_user.id
    ).first()
    appointment = (
        Appointment.query.join(AppointmentSlot)
        .filter(
            Appointment.id == appointment_id,
            AppointmentSlot.faculty_id == faculty_member.id
        )
        .first()
    )
    if not appointment:
        flash("Appointment not found.", "danger")
        return redirect(url_for("faculty.appointments"))

    if action == "accept":
        appointment.status = "accepted"
        flash("Appointment accepted.", "success")
    elif action == "reject":
        appointment.status = "rejected"
        flash("Appointment rejected.", "warning")
    elif action == "complete":
        appointment.status = "completed"
        flash("Appointment marked as completed.", "success")
    else:
        flash("Invalid action.", "danger")

    db.session.commit()
    return redirect(url_for("faculty.appointments"))