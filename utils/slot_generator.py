from datetime import date, timedelta
from models import db
from models.faculty import Faculty
from models.faculty_timetable import FacultyTimetable
from models.schedule_period import SchedulePeriod
from models.appointment_slot import AppointmentSlot

def generate_slots_for_faculty(faculty_id, start_date=None, days=14):
    """
    Generate appointment slots for a faculty member.
    - Excludes Sundays (working days are Monday to Saturday).
    - Removes truly empty slots (zero appointment history) if a lecture is scheduled.
    - Avoids deleting slots that have past, completed, or cancelled appointment references.
    """
    if start_date is None:
        start_date = date.today()

    faculty = db.session.get(Faculty, faculty_id)
    if not faculty:
        return 0

    periods = SchedulePeriod.query.order_by(SchedulePeriod.order).all()
    created_count = 0

    for day_offset in range(days):
        current_date = start_date + timedelta(days=day_offset)
        # Monday = 0 ... Saturday = 5, Sunday = 6
        day_of_week = current_date.weekday()

        # Skip Sunday
        if day_of_week > 5:
            sunday_slots = AppointmentSlot.query.filter_by(
                faculty_id=faculty.id,
                date=current_date
            ).all()
            for s_slot in sunday_slots:
                # Only delete if there are absolutely NO appointments tied to this slot
                if not s_slot.appointments:
                    db.session.delete(s_slot)
            continue

        # Get periods where faculty has lectures
        lecture_entries = FacultyTimetable.query.filter_by(
            faculty_id=faculty.id,
            day_of_week=day_of_week
        ).all()
        lecture_period_ids = {entry.period_id for entry in lecture_entries}

        for period in periods:
            existing_slot = AppointmentSlot.query.filter_by(
                faculty_id=faculty.id,
                period_id=period.id,
                date=current_date
            ).first()

            # Faculty has a lecture in this period
            if period.id in lecture_period_ids:
                # Only delete the slot if no appointments ever referenced it
                if existing_slot and not existing_slot.appointments:
                    db.session.delete(existing_slot)
                continue

            # If slot already exists, keep it
            if existing_slot:
                continue

            # Period is free, create new slot
            slot = AppointmentSlot(
                faculty_id=faculty.id,
                period_id=period.id,
                date=current_date,
                capacity=5
            )
            db.session.add(slot)
            created_count += 1

    db.session.commit()
    return created_count