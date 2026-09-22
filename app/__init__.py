from flask import Flask, render_template
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


def ensure_adoption_content_columns():
    for table in ("adoptions", "adoption_requests"):
        columns = {column["name"] for column in inspect(db.engine).get_columns(table)}
        with db.engine.begin() as connection:
            if "plaque_text" not in columns:
                connection.execute(text(f"ALTER TABLE {table} ADD COLUMN plaque_text TEXT"))
            if "in_memory_name" not in columns:
                connection.execute(text(f"ALTER TABLE {table} ADD COLUMN in_memory_name TEXT"))
            if "dedication" in columns:
                connection.execute(
                    text(
                        f"UPDATE {table} SET plaque_text = dedication "
                        "WHERE plaque_text IS NULL AND dedication IS NOT NULL"
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
                "(bench_id, adopter_name, adopter_email, adoption_type, plaque_text, "
                "in_memory_name, requested_location, show_name, start_date, end_date) "
                "SELECT bench_id, adopter_name, adopter_email, adoption_type, plaque_text, "
                "in_memory_name, "
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
        ensure_adoption_content_columns()
        migrate_legacy_adoption_requests()
        normalize_bench_codes()

    @app.errorhandler(404)
    def page_not_found(error):
        return render_template("404.html"), 404

    return app


app = create_app()
