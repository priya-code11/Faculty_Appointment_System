from models import db
from datetime import datetime
import uuid


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

    slot_id = db.Column(
        db.String(36),
        db.ForeignKey("appointment_slots.id"),
        nullable=False
    )

    reason = db.Column(
        db.Text,
        nullable=False
    )

    status = db.Column(
        db.String(20),
        default="pending",
        nullable=False
    )

    created_at = db.Column(
        db.DateTime,
        default=datetime.utcnow,
        nullable=False
    )

    student = db.relationship(
        "Student",
        backref=db.backref(
            "appointments",
            lazy=True
        )
    )

    slot = db.relationship(
        "AppointmentSlot",
        backref=db.backref(
            "appointments",
            lazy=True
        )
    )

    def __repr__(self):
        return f"<Appointment {self.id}>"