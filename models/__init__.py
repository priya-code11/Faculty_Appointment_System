from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()


def init_models():

    from models.user import User
    from models.student import Student
    from models.faculty import Faculty
    from models.schedule_period import SchedulePeriod
    from models.faculty_timetable import FacultyTimetable
    from models.appointment_slot import AppointmentSlot
    from models.appointment import Appointment