from flask import Flask
from flask_sqlalchemy import SQLAlchemy

from .config import Config

db = SQLAlchemy()


def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)

    db.init_app(app)

    from .api import api
    from .site import site

    app.register_blueprint(api)
    app.register_blueprint(site)

    with app.app_context():
        from app import models
        db.create_all()

    return app


app = create_app()
