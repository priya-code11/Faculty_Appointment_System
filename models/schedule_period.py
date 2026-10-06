from models import db
import uuid


class SchedulePeriod(db.Model):
    __tablename__ = "schedule_periods"

    id = db.Column(
        db.String(36),
        primary_key=True,
        default=lambda: str(uuid.uuid4())
    )

    name = db.Column(
        db.String(50),
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

    # Used to display periods in correct order
    order = db.Column(
        db.Integer,
        nullable=False
    )

    def __repr__(self):
        return f"<SchedulePeriod {self.name}>"