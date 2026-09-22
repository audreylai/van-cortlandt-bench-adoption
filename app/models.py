from datetime import date

from . import db

class Bench(db.Model):
    __tablename__ = "benches"
    __table_args__ = (
        db.CheckConstraint(
            "bench_type IN ('World''s Fair', 'Concrete base')",
            name="valid_bench_type",
        ),
    )

    bench_id = db.Column(db.Integer, primary_key=True)
    code = db.Column(db.Text, unique=True, nullable=False)
    location = db.Column(db.Text, nullable=False)
    bench_type = db.Column(
        db.Text, nullable=False, default="Concrete base", server_default="Concrete base"
    )
    adoptions = db.relationship(
        "Adoption", back_populates="bench", cascade="all, delete-orphan"
    )
    adoption_requests = db.relationship(
        "AdoptionRequest", back_populates="bench", cascade="all, delete-orphan"
    )


class Adoption(db.Model):
    __tablename__ = "adoptions"
    __table_args__ = (
        db.CheckConstraint(
            "adoption_type IN ('bench_adoption', 'new_bench')",
            name="valid_adoption_type",
        ),
    )

    adoption_id = db.Column(db.Integer, primary_key=True)
    bench_id = db.Column(
        db.Integer, db.ForeignKey("benches.bench_id"), nullable=True
    )
    adopter_name = db.Column(db.Text, nullable=False)
    adopter_email = db.Column(db.Text, nullable=False)
    adoption_type = db.Column(db.Text, nullable=False)
    plaque_text = db.Column(db.Text)
    in_memory_name = db.Column(db.Text)
    requested_location = db.Column(db.Text)
    show_name = db.Column(db.Boolean, nullable=False, default=True, server_default="true")
    start_date = db.Column(db.Date, nullable=False, default=date.today)
    end_date = db.Column(db.Date, nullable=False)
    bench = db.relationship("Bench", back_populates="adoptions")


class AdoptionRequest(db.Model):
    __tablename__ = "adoption_requests"
    __table_args__ = (
        db.CheckConstraint(
            "adoption_type IN ('bench_adoption', 'new_bench')",
            name="valid_adoption_request_type",
        ),
    )

    request_id = db.Column(db.Integer, primary_key=True)
    bench_id = db.Column(db.Integer, db.ForeignKey("benches.bench_id"))
    adopter_name = db.Column(db.Text, nullable=False)
    adopter_email = db.Column(db.Text, nullable=False)
    adoption_type = db.Column(db.Text, nullable=False)
    plaque_text = db.Column(db.Text)
    in_memory_name = db.Column(db.Text)
    requested_location = db.Column(db.Text)
    show_name = db.Column(db.Boolean, nullable=False, default=True, server_default="true")
    plaque_timing_acknowledged = db.Column(
        db.Boolean, nullable=False, default=False, server_default="false"
    )
    requested_date = db.Column(db.Date, nullable=False, default=date.today)
    start_date = db.Column(db.Date, nullable=False, default=date.today)
    end_date = db.Column(db.Date, nullable=False)
    bench = db.relationship("Bench", back_populates="adoption_requests")
