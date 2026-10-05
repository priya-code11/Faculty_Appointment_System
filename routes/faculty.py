from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user
from models import db
from models.availability import Availability
from models.appointment import Appointment


faculty = Blueprint(
    "faculty",
    __name__,
    url_prefix="/faculty"
)


@faculty.route("/dashboard")
@login_required
def dashboard():

    if current_user.role != "faculty":
        return "Unauthorized", 403

    return render_template(
        "faculty/dashboard.html",
        user=current_user
    )


@faculty.route("/availability", methods=["GET", "POST"])
@login_required
def availability():

    if current_user.role != "faculty":
        return "Unauthorized", 403

    # Get faculty profile
    faculty_profile = current_user.faculty

    if request.method == "POST":

        date = request.form["date"]
        start_time = request.form["start_time"]
        end_time = request.form["end_time"]

        slot = Availability(
            faculty_id=faculty_profile.id,
            date=date,
            start_time=start_time,
            end_time=end_time,
            status="available"
        )

        db.session.add(slot)
        db.session.commit()

        flash("Availability added successfully.")

        return redirect(url_for("faculty.availability"))

    slots = Availability.query.filter_by(
        faculty_id=faculty_profile.id
    ).order_by(
        Availability.date,
        Availability.start_time
    ).all()

    return render_template(
        "faculty/availability.html",
        slots=slots
    )

@faculty.route("/appointments")
@login_required
def appointments():

    if current_user.role != "faculty":
        return "Unauthorized", 403

    faculty_profile = current_user.faculty

    appointments = Appointment.query.filter_by(
        faculty_id=faculty_profile.id
    ).order_by(
        Appointment.date,
        Appointment.start_time
    ).all()

    return render_template(
        "faculty/appointments.html",
        appointments=appointments
    )


@faculty.route(
    "/appointment/<string:appointment_id>/<string:action>",
    methods=["POST"]
)
@login_required
def update_appointment(appointment_id, action):

    if current_user.role != "faculty":
        return "Unauthorized", 403

    faculty_profile = current_user.faculty

    appointment = Appointment.query.get_or_404(
        appointment_id
    )

    if appointment.faculty_id != faculty_profile.id:
        return "Unauthorized", 403

    if action == "accept":

        appointment.status = "accepted"

    elif action == "reject":

        appointment.status = "rejected"

        slot = Availability.query.filter_by(
            faculty_id=appointment.faculty_id,
            date=appointment.date,
            start_time=appointment.start_time,
            end_time=appointment.end_time
        ).first()

        if slot:
            slot.status = "available"

    elif action == "complete":

        appointment.status = "completed"

    else:

        return "Invalid action", 400

    db.session.commit()

    flash("Appointment status updated.")

    return redirect(
        url_for("faculty.appointments")
    )