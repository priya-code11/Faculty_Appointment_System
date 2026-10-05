from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user
from models import db
from models.faculty import Faculty
from models.availability import Availability
from models.appointment import Appointment
from datetime import date


student = Blueprint(
    "student",
    __name__,
    url_prefix="/student"
)


@student.route("/dashboard")
@login_required
def dashboard():

    if current_user.role != "student":
        return "Unauthorized", 403

    student_profile = current_user.student

    appointments = Appointment.query.filter_by(
        student_id=student_profile.id
    ).order_by(
        Appointment.date.desc(),
        Appointment.start_time.desc()
    ).all()

    return render_template(
        "student/dashboard.html",
        user=current_user,
        appointments=appointments
    )


@student.route("/faculty")
@login_required
def faculty_list():

    if current_user.role != "student":
        return "Unauthorized", 403

    faculty_members = Faculty.query.all()

    return render_template(
        "student/faculty_list.html",
        faculty_members=faculty_members
    )


@student.route("/faculty/<string:faculty_id>/availability")
@login_required
def faculty_availability(faculty_id):

    if current_user.role != "student":
        return "Unauthorized", 403

    faculty_member = Faculty.query.get_or_404(faculty_id)

    slots = Availability.query.filter(
        Availability.faculty_id == faculty_id,
        Availability.date >= date.today(),
        Availability.status == "available"
    ).order_by(
        Availability.date,
        Availability.start_time
    ).all()

    return render_template(
        "student/book_appointment.html",
        faculty=faculty_member,
        slots=slots
    )


@student.route("/book/<string:availability_id>", methods=["POST"])
@login_required
def book_appointment(availability_id):

    if current_user.role != "student":
        return "Unauthorized", 403

    student_profile = current_user.student

    slot = Availability.query.get_or_404(availability_id)

    if slot.status != "available":
        flash("This slot is no longer available.")
        return redirect(
            url_for(
                "student.faculty_availability",
                faculty_id=slot.faculty_id
            )
        )

    reason = request.form.get("reason")

    if not reason:
        flash("Please enter a reason for the appointment.")
        return redirect(
            url_for(
                "student.faculty_availability",
                faculty_id=slot.faculty_id
            )
        )

    # Check whether the student already has an appointment
    # for this exact slot.
    existing = Appointment.query.filter_by(
        student_id=student_profile.id,
        faculty_id=slot.faculty_id,
        date=slot.date,
        start_time=slot.start_time,
        end_time=slot.end_time
    ).first()

    if existing:
        flash("You have already booked this slot.")
        return redirect(url_for("student.appointments"))

    appointment = Appointment(
        student_id=student_profile.id,
        faculty_id=slot.faculty_id,
        date=slot.date,
        start_time=slot.start_time,
        end_time=slot.end_time,
        reason=reason,
        status="pending"
    )

    # Mark slot as unavailable
    slot.status = "booked"

    db.session.add(appointment)
    db.session.commit()

    flash("Appointment booked successfully.")

    return redirect(url_for("student.appointments"))


@student.route("/appointments")
@login_required
def appointments():

    if current_user.role != "student":
        return "Unauthorized", 403

    student_profile = current_user.student

    appointments = Appointment.query.filter_by(
        student_id=student_profile.id
    ).order_by(
        Appointment.date.desc(),
        Appointment.start_time.desc()
    ).all()

    return render_template(
        "student/appointments.html",
        appointments=appointments
    )


@student.route("/appointment/<string:appointment_id>/cancel", methods=["POST"])
@login_required
def cancel_appointment(appointment_id):

    if current_user.role != "student":
        return "Unauthorized", 403

    student_profile = current_user.student

    appointment = Appointment.query.get_or_404(
        appointment_id
    )

    if appointment.student_id != student_profile.id:
        return "Unauthorized", 403

    if appointment.status not in ["pending", "accepted"]:
        flash("This appointment cannot be cancelled.")
        return redirect(url_for("student.appointments"))

    # Make the original slot available again
    slot = Availability.query.filter_by(
        faculty_id=appointment.faculty_id,
        date=appointment.date,
        start_time=appointment.start_time,
        end_time=appointment.end_time
    ).first()

    if slot:
        slot.status = "available"

    appointment.status = "cancelled"

    db.session.commit()

    flash("Appointment cancelled.")

    return redirect(url_for("student.appointments"))