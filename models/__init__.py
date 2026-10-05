from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

def init_models():
    from models.user import User
    from models.student import Student
    from models.faculty import Faculty
    from models.availability import Availability
    from models.appointment import Appointment