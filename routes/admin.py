from flask import Blueprint, render_template
from flask_login import login_required, current_user
from sqlalchemy.orm import joinedload
from models.user import User
from models.student import Student
from models.faculty import Faculty
from models.appointment import Appointment
from models.appointment_slot import AppointmentSlot

admin = Blueprint(
    "admin",
    __name__,
    url_prefix="/admin"
)

def admin_required():
    return current_user.is_authenticated and current_user.role == "admin"

@admin.route("/dashboard")
@login_required
def dashboard():
    if not admin_required():
        return "Unauthorized", 403

    # Primary entity metrics
    total_users = User.query.count()
    total_students = Student.query.count()
    total_faculty = Faculty.query.count()
    total_appointments = Appointment.query.count()

    # Appointment status breakdown
    pending_appointments = Appointment.query.filter_by(status="pending").count()
    accepted_appointments = Appointment.query.filter_by(status="accepted").count()
    completed_appointments = Appointment.query.filter_by(status="completed").count()
    cancelled_appointments = Appointment.query.filter_by(status="cancelled").count()

    # Total generated consultation slots
    total_slots = AppointmentSlot.query.count()

    # Recent 5 appointments with eager-loaded relations
    recent_appointments = (
        Appointment.query.options(
            joinedload(Appointment.student).joinedload(Student.user),
            joinedload(Appointment.slot).joinedload(AppointmentSlot.faculty).joinedload(Faculty.user),
            joinedload(Appointment.slot).joinedload(AppointmentSlot.period),
        )
        .order_by(Appointment.created_at.desc())
        .limit(5)
        .all()
    )

    return render_template(
        "admin/dashboard.html",
        total_users=total_users,
        total_students=total_students,
        total_faculty=total_faculty,
        total_appointments=total_appointments,
        pending_appointments=pending_appointments,
        accepted_appointments=accepted_appointments,
        completed_appointments=completed_appointments,
        cancelled_appointments=cancelled_appointments,
        total_slots=total_slots,
        recent_appointments=recent_appointments
    )

@admin.route("/students")
@login_required
def students():
    if not admin_required():
        return "Unauthorized", 403
    students = Student.query.all()
    return render_template(
        "admin/students.html",
        students=students
    )

@admin.route("/faculty")
@login_required
def faculty():
    if not admin_required():
        return "Unauthorized", 403
    faculty_members = Faculty.query.all()
    return render_template(
        "admin/faculty.html",
        faculty_members=faculty_members
    )

@admin.route("/appointments")
@login_required
def appointments():
    if not admin_required():
        return "Unauthorized", 403
    appointments = (
        Appointment.query.join(AppointmentSlot)
        .order_by(AppointmentSlot.date.desc(), Appointment.created_at.desc())
        .all()
    )
    return render_template(
        "admin/appointments.html",
        appointments=appointments
    )