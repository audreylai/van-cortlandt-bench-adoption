import calendar
from datetime import date, timedelta

from flask import Blueprint, jsonify, request
from sqlalchemy import func

from . import db
from .mail import send_request_received
from .models import Adoption, AdoptionRequest, Bench

api = Blueprint("api", __name__, url_prefix="/api")

# TODO : Move these constants to a config file or database table and allow admin editing via a secure admin interface. For now, they are hardcoded for simplicity.
ADOPTION_OPTIONS = {
    "bench_adoption": {"label": "Bench Adoption", "price": 3500},
    "new_bench": {"label": "Install a new bench", "price": 5500},
}
ADOPTION_TERM_MONTHS = 120


def add_months(start_date, months):
    month_index = start_date.month - 1 + months
    year = start_date.year + month_index // 12
    month = month_index % 12 + 1
    day = min(start_date.day, calendar.monthrange(year, month)[1])
    return date(year, month, day)


def adoption_end_date(start_date, adoption_type):
    return add_months(start_date, ADOPTION_TERM_MONTHS) - timedelta(days=1)


def current_adoption(bench):
    today = date.today()
    return next(
        (
            adoption
            for adoption in bench.adoptions
            if adoption.end_date >= today
        ),
        None,
    )


def serialize_bench(bench):
    adoption = current_adoption(bench)
    response = {
        "bench_id": bench.bench_id,
        "code": bench.code,
        "location": bench.location,
        "bench_type": bench.bench_type,
        "available": adoption is None,
    }

    if adoption:
        response["adoption"] = {
            "adoption_id": adoption.adoption_id,
            "adoption_type": adoption.adoption_type,
            "price": ADOPTION_OPTIONS[adoption.adoption_type]["price"],
            "price_note": "and up" if adoption.adoption_type == "new_bench" else None,
            "adopter_name": adoption.adopter_name,
            "adopter_email": adoption.adopter_email,
            "start_date": adoption.start_date.isoformat(),
            "end_date": adoption.end_date.isoformat(),
            "term_years": 10,
        }

    return response


@api.get("/benches")
def benches():
    all_benches = Bench.query.order_by(Bench.bench_id).all()
    return jsonify([serialize_bench(bench) for bench in all_benches])


@api.get("/bench/<int:bench_id>")
def bench(bench_id):
    bench_record = db.get_or_404(Bench, bench_id)
    return jsonify(serialize_bench(bench_record))


@api.post("/bench/<int:bench_id>/adopt")
def adopt_bench(bench_id):
    bench_record = db.get_or_404(Bench, bench_id)
    if current_adoption(bench_record):
        return jsonify(error="bench is already adopted"), 409

	# Todo: when implementing file uploads, need to use request.files for file data
    payload = request.get_json(silent=True) or request.form
    adopter_name = payload.get("adopter_name")
    adopter_email = (payload.get("adopter_email") or "").strip().lower()
    adoption_type = payload.get("adoption_type")
    plaque_text = payload.get("plaque_text")
    in_memory_name = payload.get("in_memory_name")
    show_name = payload.get("show_name", True)
    
    # form validation
    if isinstance(show_name, str):
        show_name = show_name.lower() in {"1", "true", "on", "yes"}

    if not adopter_name or not adopter_email:
        return jsonify(error="adopter_name and adopter_email are required"), 400

    if adoption_type != "bench_adoption":
        return jsonify(error="Use the public adoption form for new bench requests"), 400

    if plaque_text is not None and len(plaque_text) > 300:
        return jsonify(error="plaque_text must be 300 characters or fewer"), 400

    if not isinstance(show_name, bool):
        return jsonify(error="show_name must be true or false"), 400

    duplicate_active = Adoption.query.filter(
        Adoption.bench_id == bench_record.bench_id,
        func.lower(Adoption.adopter_email) == adopter_email,
    ).first()
    duplicate_request = AdoptionRequest.query.filter(
        AdoptionRequest.bench_id == bench_record.bench_id,
        func.lower(AdoptionRequest.adopter_email) == adopter_email,
    ).first()
    if duplicate_active or duplicate_request:
        return jsonify(error="email is already associated with a request for this bench"), 409

    start_date = date.today()
    adoption = AdoptionRequest(
        bench=bench_record,
        adopter_name=adopter_name,
        adopter_email=adopter_email,
        adoption_type=adoption_type,
        plaque_text=plaque_text,
        in_memory_name=in_memory_name,
        show_name=show_name,
        requested_date=date.today(),
        start_date=start_date,
        end_date=adoption_end_date(start_date, adoption_type),
    )
    db.session.add(adoption)
    db.session.commit()
    send_request_received(adoption)

    return jsonify(serialize_bench(bench_record)), 201
