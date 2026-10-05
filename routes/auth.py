from flask import Blueprint, render_template, request, redirect, url_for, flash
from models import db
from models.user import User
from models.student import Student
from models.faculty import Faculty
from flask_login import login_user, logout_user


auth = Blueprint("auth", __name__)


@auth.route("/register", methods=["GET", "POST"])
def register():

    if request.method == "POST":

        name = request.form["name"]
        email = request.form["email"]
        password = request.form["password"]
        role = request.form["role"]

        # Check existing email
        existing_user = User.query.filter_by(email=email).first()

        if existing_user:
            flash("Email already registered.")
            return redirect(url_for("auth.register"))


        # Create User
        user = User(
            name=name,
            email=email,
            role=role
        )

        user.set_password(password)

        db.session.add(user)
        db.session.flush()


        # Create Student Profile
        if role == "student":

            enrollment_no = request.form["enrollment_no"]
            department = request.form["student_department"]
            semester = request.form["semester"]

            student = Student(
                user_id=user.id,
                enrollment_no=enrollment_no,
                department=department,
                semester=semester
            )

            db.session.add(student)


        # Create Faculty Profile
        elif role == "faculty":

            department = request.form["faculty_department"]
            designation = request.form["designation"]
            specialization = request.form["specialization"]

            faculty = Faculty(
                user_id=user.id,
                department=department,
                designation=designation,
                specialization=specialization
            )

            db.session.add(faculty)

        elif user.role == "admin":
            return redirect(url_for("admin.dashboard"))

        db.session.commit()

        flash("Registration successful. Please login.")

        return redirect(url_for("auth.login"))


    return render_template("auth/register.html")


@auth.route("/login", methods=["GET", "POST"])
def login():

    if request.method == "POST":

        email = request.form["email"]
        password = request.form["password"]

        user = User.query.filter_by(email=email).first()

        if user and user.check_password(password):

            login_user(user)

            if user.role == "student":
                return redirect(url_for("student.dashboard"))

            elif user.role == "faculty":
                return redirect(url_for("faculty.dashboard"))

            elif user.role == "admin":
                return redirect(url_for("admin.dashboard"))

        flash("Invalid email or password.")

    return render_template("auth/login.html")


@auth.route("/logout")
def logout():

    logout_user()

    return redirect(url_for("auth.login"))