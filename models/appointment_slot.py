from models import db
import uuid


class AppointmentSlot(db.Model):
    __tablename__ = "appointment_slots"

    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    faculty_id = db.Column(db.String(36), db.ForeignKey("faculty.id"), nullable=False)
    period_id = db.Column(db.String(36), db.ForeignKey("schedule_periods.id"), nullable=False)
    date = db.Column(db.Date, nullable=False)
    capacity = db.Column(db.Integer, default=5, nullable=False)

    faculty = db.relationship("Faculty", backref=db.backref("appointment_slots", lazy=True))
    period = db.relationship("SchedulePeriod", backref=db.backref("appointment_slots", lazy=True))

    @property
    def booked_count(self):
        """Number of pending or accepted bookings consuming capacity."""
        return sum(
            appointment.status in ("pending", "accepted")
            for appointment in self.appointments
        )

    @property
    def remaining_capacity(self):
        return self.capacity - self.booked_count

    @property
    def is_full(self):
        return self.booked_count >= self.capacity

    def __repr__(self):
        return f"<AppointmentSlot {self.id}>"
