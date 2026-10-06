from models import db
import uuid


class FacultyTimetable(db.Model):
    __tablename__ = "faculty_timetable"

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

    period_id = db.Column(
        db.String(36),
        db.ForeignKey("schedule_periods.id"),
        nullable=False
    )

    # 0 = Monday
    # 1 = Tuesday
    # 2 = Wednesday
    # 3 = Thursday
    # 4 = Friday
    # 5 = Saturday
    # 6 = Sunday
    day_of_week = db.Column(
        db.Integer,
        nullable=False
    )

    subject = db.Column(
        db.String(100)
    )

    faculty = db.relationship(
        "Faculty",
        backref=db.backref("timetable_entries", lazy=True)
    )

    period = db.relationship(
        "SchedulePeriod",
        backref=db.backref("timetable_entries", lazy=True)
    )

    def __repr__(self):
        return f"<FacultyTimetable {self.id}>"