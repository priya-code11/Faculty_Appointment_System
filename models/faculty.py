from models import db
import uuid


class Faculty(db.Model):
    __tablename__ = "faculty"

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

    department = db.Column(
        db.String(100),
        nullable=False
    )

    designation = db.Column(
        db.String(100),
        nullable=False
    )

    specialization = db.Column(
        db.String(200)
    )

    user = db.relationship(
        "User",
        backref=db.backref("faculty", uselist=False)
    )