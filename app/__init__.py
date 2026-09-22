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


def ensure_adoption_request_columns():
    columns = {
        column["name"]
        for column in inspect(db.engine).get_columns("adoptions")
    }
    with db.engine.begin() as connection:
        if "requested_location" not in columns:
            connection.execute(
                text("ALTER TABLE adoptions ADD COLUMN requested_location TEXT")
            )
        if db.engine.dialect.name == "postgresql":
            connection.execute(
                text("ALTER TABLE adoptions ALTER COLUMN bench_id DROP NOT NULL")
            )


def ensure_request_date_column():
    columns = {
        column["name"]
        for column in inspect(db.engine).get_columns("adoption_requests")
    }
    if "requested_date" not in columns:
        with db.engine.begin() as connection:
            connection.execute(
                text(
                    "ALTER TABLE adoption_requests ADD COLUMN requested_date DATE"
                )
            )
            connection.execute(
                text(
                    "UPDATE adoption_requests SET requested_date = CURRENT_DATE "
                    "WHERE requested_date IS NULL"
                )
            )


def migrate_legacy_adoption_requests():
    columns = {
        column["name"]
        for column in inspect(db.engine).get_columns("adoptions")
    }
    if "approved" not in columns:
        return

    requested_location = "requested_location" if "requested_location" in columns else "NULL"
    with db.engine.begin() as connection:
        connection.execute(
            text(
                "INSERT INTO adoption_requests "
                "(bench_id, adopter_name, adopter_email, adoption_type, dedication, "
                "requested_location, show_name, start_date, end_date) "
                "SELECT bench_id, adopter_name, adopter_email, adoption_type, dedication, "
                f"{requested_location}, show_name, start_date, end_date "
                "FROM adoptions WHERE approved = FALSE"
            )
        )
        connection.execute(text("DELETE FROM adoptions WHERE approved = FALSE"))


def normalize_bench_codes():
    with db.engine.begin() as connection:
        connection.execute(
            text(
                "UPDATE benches SET code = SUBSTR(code, 5) "
                "WHERE code LIKE 'VCP-%'"
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
        ensure_adoption_request_columns()
        ensure_request_date_column()
        migrate_legacy_adoption_requests()
        normalize_bench_codes()

    return app


app = create_app()
