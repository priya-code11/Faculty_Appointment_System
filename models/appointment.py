import uuid

from models import db
from datetime import datetime



class Appointment(db.Model):
    __tablename__ = "appointments"

    id = db.Column(
        db.String(36),
        primary_key=True,
        default=lambda: str(uuid.uuid4())
    )

    student_id = db.Column(
        db.String(36),
        db.ForeignKey("students.id"),
        nullable=False
    )

    faculty_id = db.Column(
        db.String(36),
        db.ForeignKey("faculty.id"),
        nullable=False
    )

    date = db.Column(
        db.Date,
        nullable=False
    )

    start_time = db.Column(
        db.Time,
        nullable=False
    )

    end_time = db.Column(
        db.Time,
        nullable=False
    )

    reason = db.Column(
        db.Text,
        nullable=False
    )

    status = db.Column(
        db.String(20),
        default="pending"
    )

    created_at = db.Column(
        db.DateTime,
        default=datetime.utcnow
    )

    student = db.relationship(
        "Student",
        backref="appointments"
    )

    faculty = db.relationship(
        "Faculty",
        backref="appointments"
    )