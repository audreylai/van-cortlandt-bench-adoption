from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import inspect, text

from .config import Config

db = SQLAlchemy()


def ensure_adoption_approval_column():
    if "approved" in {
        column["name"] for column in inspect(db.engine).get_columns("adoptions")
    }:
        return

    with db.engine.begin() as connection:
        connection.execute(
            text(
                "ALTER TABLE adoptions "
                "ADD COLUMN approved BOOLEAN NOT NULL DEFAULT TRUE"
            )
        )


def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)

    db.init_app(app)

    from .api import api
    from .admin import admin
    from .site import site

    app.register_blueprint(api)
    app.register_blueprint(admin)
    app.register_blueprint(site)

    with app.app_context():
        from app import models
        db.create_all()
        ensure_adoption_approval_column()

    return app


app = create_app()
