from datetime import date

from . import db


class Bench(db.Model):
    __tablename__ = "benches"

    bench_id = db.Column(db.Integer, primary_key=True)
    code = db.Column(db.Text, unique=True, nullable=False)
    location = db.Column(db.Text, nullable=False)
    adoptions = db.relationship(
        "Adoption", back_populates="bench", cascade="all, delete-orphan"
    )


class Adoption(db.Model):
    __tablename__ = "adoptions"

    adoption_id = db.Column(db.Integer, primary_key=True)
    bench_id = db.Column(
        db.Integer, db.ForeignKey("benches.bench_id"), nullable=False
    )
    adopter_name = db.Column(db.Text, nullable=False)
    adopter_email = db.Column(db.Text, nullable=False)
    start_date = db.Column(db.Date, nullable=False, default=date.today)
    end_date = db.Column(db.Date, nullable=False)
    bench = db.relationship("Bench", back_populates="adoptions")
