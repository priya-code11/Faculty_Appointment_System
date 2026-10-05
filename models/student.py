from models import db
import uuid


class Student(db.Model):
    __tablename__ = "students"

    id = db.Column(
        db.String(36),
        primary_key=True,
        default=lambda: str(uuid.uuid4())
    )

    user_id = db.Column(
        db.String(36),
        db.ForeignKey("users.id"),
        nullable=False,
        unique=True
    )

    enrollment_no = db.Column(
        db.String(50),
        unique=True,
        nullable=False
    )

    department = db.Column(
        db.String(100),
        nullable=False
    )

    semester = db.Column(
        db.Integer,
        nullable=False
    )

    user = db.relationship(
        "User",
        backref=db.backref("student", uselist=False)
    )