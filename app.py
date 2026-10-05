from flask import Flask
from config import Config
from models import db, init_models
from flask_login import LoginManager
from models.user import User

from routes.auth import auth
from routes.admin import admin
from routes.student import student
from routes.faculty import faculty


def create_app():

    app = Flask(__name__)

    app.config.from_object(Config)

    db.init_app(app)

    login_manager = LoginManager()
    login_manager.init_app(app)
    login_manager.login_view = "auth.login"

    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(str(user_id))

    init_models()

    with app.app_context():
        db.create_all()

    app.register_blueprint(auth)
    app.register_blueprint(admin)
    app.register_blueprint(student)
    app.register_blueprint(faculty)
    
    @app.route("/")
    def home():
        return "Faculty Appointment System is running!"

    return app


app = create_app()


if __name__ == "__main__":
    app.run(debug=True)