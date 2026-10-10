# Faculty Appointment Booking System

An academic scheduling portal built with Flask, PostgreSQL, and Bootstrap 5. The platform automatically calculates faculty consultation slots directly from weekly teaching timetables, preventing double-booking and enabling students to reserve 1-on-1 consultations.

---

## Features

### Role-Based Access Control

* **Students:** Browse faculty directories, view real-time availability calendars, book consultation periods, track approval statuses, cancel bookings, and export scheduled appointments to `.ics` or Google Calendar.


* **Faculty:** Build weekly recurring lecture timetables (Monday–Saturday), toggle overall availability ("Available" vs. "Busy"), review appointment requests (Accept / Reject / Complete), and view daily lecture/appointment agendas.


* **Administrators:** View system-wide analytics, monitor all student and faculty profiles, and oversee all appointment statuses.



### Automatic Slot Calculation

* **Timetable Sync:** Appointment slots are generated automatically for the next 14 days based on the master periods defined in the database.


* **No Double-Booking:** Any period marked with a lecture in the faculty member's timetable is excluded from slot generation.


* **Capacity Management:** Each slot supports multi-student capacity tracking (default: 5 students).



---

## Tech Stack

* **Backend:** Python 3, Flask, Flask-SQLAlchemy, Flask-Login, Werkzeug


* **Database:** PostgreSQL (with `psycopg` / `psycopg2`)


* **Frontend:** Jinja2 templates, Bootstrap 5, Bootstrap Icons



---

## Project Structure

```text
Faculty_Appointment_System/
│
├── app.py                      # Application factory and entry point
├── config.py                   # Environment configuration
├── requirements.txt            # Python dependencies
├── .env                        # Database connection string and secrets
│
├── models/                     # SQLAlchemy data models
│   ├── appointment.py          # Student appointment reservations
│   ├── appointment_slot.py     # Generated consultation slots
│   ├── faculty.py              # Faculty profile
│   ├── faculty_timetable.py    # Weekly lecture schedules
│   ├── schedule_period.py      # Master campus time slots
│   ├── student.py              # Student profile
│   └── user.py                 # Core user accounts and authentication
│
├── routes/                     # Blueprint route handlers
│   ├── admin.py                # Admin dashboard and user management
│   ├── auth.py                 # Login, registration, and logout
│   ├── faculty.py              # Timetable, availability, and requests
│   └── student.py              # Slot browsing, booking, and history
│
├── utils/                      # Helper modules (Automated slot generation algorithm)
│   └── slot_generator.py       
│   └── generate_slots.php      
│
├── static/                     # CSS, JavaScript, and static assets
│   ├── css/style.css           # Custom stylesheets
│   └── js/script.js            # UI interactions and confirmation handlers
│
└── templates/                  # Jinja2 HTML templates
    ├── admin/                  # Admin views
    ├── auth/                   # Authentication views
    ├── faculty/                # Faculty views
    └── student/                # Student views

```

---

## Getting Started

### Prerequisites

* Python 3.10+
* PostgreSQL running locally or remotely

### 1. Clone the Repository

```bash
git clone https://github.com/priya-code11/Faculty_Appointment_System.git
cd Faculty_Appointment_System

```

### 2. Create and Activate a Virtual Environment

* **Windows (PowerShell):**
```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1

```


* **macOS / Linux:**
```bash
python3 -m venv .venv
source .venv/bin/activate

```



### 3. Install Dependencies

```bash
pip install -r requirements.txt

```

### 4. Configure Environment Variables

Create a `.env` file in the root directory and specify your database connection details:

```env
SECRET_KEY="your-secret-key-here"
DATABASE_URL="postgresql://username:password@localhost:5432/faculty_appointment_db"

```

### 5. Initialize the Database and Seed Master Periods

Create the database in PostgreSQL:

```sql
CREATE DATABASE faculty_appointment_db;

```

Open a Python shell to initialize the tables and seed academic schedule periods:

```python
from app import create_app
from models import db
from models.schedule_period import SchedulePeriod
from datetime import time

app = create_app()

with app.app_context():
    db.create_all()

    # Seed master lecture periods if empty
    if SchedulePeriod.query.count() == 0:
        periods = [
            SchedulePeriod(name="Period 1", start_time=time(9, 0), end_time=time(10, 0), order=1),
            SchedulePeriod(name="Period 2", start_time=time(10, 0), end_time=time(11, 0), order=2),
            SchedulePeriod(name="Period 3", start_time=time(11, 15), end_time=time(12, 15), order=3),
            SchedulePeriod(name="Period 4", start_time=time(12, 15), end_time=time(13, 15), order=4),
            SchedulePeriod(name="Period 5", start_time=time(14, 0), end_time=time(15, 0), order=5),
            SchedulePeriod(name="Period 6", start_time=time(15, 0), end_time=time(16, 0), order=6),
        ]
        db.session.bulk_save_objects(periods)
        db.session.commit()
        print("Schedule periods initialized.")

```

### 6. Create an Admin Account

Run the following inside your Python shell to bootstrap an administrator account:

```python
from app import create_app
from models import db
from models.user import User

app = create_app()

with app.app_context():
    if not User.query.filter_by(email="admin@example.com").first():
        admin = User(name="System Admin", email="admin@example.com", role="admin")
        admin.set_password("Admin@123")
        db.session.add(admin)
        db.session.commit()
        print("Admin user created.")

```

### 7. Run the Application

```bash
python app.py

```

The application will be accessible at `[http://127.0.0.1:5000/](http://127.0.0.1:5000/)`.
