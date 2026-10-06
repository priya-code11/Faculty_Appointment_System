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

    # Faculty can turn appointment booking ON/OFF
    is_available = db.Column(
        db.Boolean,
        default=True,
        nullable=False
    )

    user = db.relationship(
        "User",
        backref=db.backref("faculty", uselist=False)
    )

    def __repr__(self):
        return f"<Faculty {self.id}>"