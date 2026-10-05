import uuid

from models import db
from datetime import date, time


class Availability(db.Model):
    __tablename__ = "availability"

    id = db.Column(
        db.String(36),
        primary_key=True,
        default=lambda: str(uuid.uuid4())
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

    status = db.Column(
        db.String(20),
        default="available"
    )

    faculty = db.relationship(
        "Faculty",
        backref="availability_slots"
    )