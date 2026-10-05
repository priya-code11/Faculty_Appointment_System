from flask import Blueprint, render_template
from flask_login import login_required, current_user
from models.user import User
from models.student import Student
from models.faculty import Faculty
from models.appointment import Appointment


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

    total_users = User.query.count()
    total_students = Student.query.count()
    total_faculty = Faculty.query.count()
    total_appointments = Appointment.query.count()

    return render_template(
        "admin/dashboard.html",
        total_users=total_users,
        total_students=total_students,
        total_faculty=total_faculty,
        total_appointments=total_appointments
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

    appointments = Appointment.query.order_by(
        Appointment.date.desc(),
        Appointment.start_time.desc()
    ).all()

    return render_template(
        "admin/appointments.html",
        appointments=appointments
    )