from datetime import date

from flask import Blueprint, redirect, render_template, request, session, url_for

from . import db
from .api import ADOPTION_OPTIONS, ADOPTION_TERM_MONTHS, add_months, current_adoption
from .models import Adoption, Bench

site = Blueprint("site", __name__)
CONFIRMATION_SESSION_KEY = "adoption_confirmation_id"


def view_bench(bench):
    adoption = next(
        (
            adoption
            for adoption in bench.adoptions
            if adoption.approved and adoption.end_date >= date.today()
        ),
        None,
    )
    view = {
        "id": bench.bench_id,
        "code": bench.code,
        "zone": bench.location,
        "bench_type": bench.bench_type,
        "adopted": adoption is not None,
        "status": "adopted" if adoption else "available",
    }

    if adoption:
        view.update(
            donor_name=adoption.adopter_name,
            donor=adoption.adopter_name,
            dedication=adoption.dedication,
            show_name=adoption.show_name,
            start_date=adoption.start_date.strftime("%b %Y"),
            end_date=adoption.end_date.strftime("%b %Y"),
            until=adoption.end_date.strftime("%b %Y"),
            days_left=max((adoption.end_date - date.today()).days, 0),
        )

    return view


@site.get("/")
def index():
    benches = [view_bench(bench) for bench in Bench.query.order_by(Bench.bench_id).all()]
    adopted_count = sum(bench["status"] == "adopted" for bench in benches)
    zones = sorted({bench["zone"] for bench in benches})
    return render_template(
        "index.html", benches=benches, adopted_count=adopted_count, zones=zones
    )


@site.get("/bench/<int:bench_id>")
def bench(bench_id):
    bench_record = db.get_or_404(Bench, bench_id)
    return render_template("bench.html", bench=view_bench(bench_record))


@site.get("/bench/<int:bench_id>/adopt")
def adopt_bench(bench_id):
    bench_record = db.get_or_404(Bench, bench_id)
    return render_template("adopt_bench.html", bench=view_bench(bench_record))


@site.post("/bench/<int:bench_id>/adopt")
def submit_adoption(bench_id):
    bench_record = db.get_or_404(Bench, bench_id)
    if current_adoption(bench_record):
        return "This bench is already adopted.", 409

    adoption_type = request.form.get("adoption_type")
    adopter_name = request.form.get("adopter_name")
    adopter_email = request.form.get("adopter_email")
    dedication = request.form.get("dedication") or None
    show_name = request.form.get("show_name") == "on"

	# basic form validation
    if not adopter_name or not adopter_email:
        return "Adopter name and email are required.", 400
    if adoption_type not in ADOPTION_OPTIONS:
        return "A valid adoption option is required.", 400

    adoption = Adoption(
        bench=bench_record,
        adopter_name=adopter_name,
        adopter_email=adopter_email,
        adoption_type=adoption_type,
        dedication=dedication,
        show_name=show_name,
        approved=False,
        start_date=date.today(),
        end_date=add_months(date.today(), ADOPTION_TERM_MONTHS),
    )
    db.session.add(adoption)
    db.session.commit()
    session[CONFIRMATION_SESSION_KEY] = adoption.adoption_id

    return redirect(
        url_for("site.adoption_confirmation", adoption_id=adoption.adoption_id),
        code=303,
    )


@site.get("/adoption/confirmation/<int:adoption_id>")
def adoption_confirmation(adoption_id):
    adoption = db.get_or_404(Adoption, adoption_id)
    if session.pop(CONFIRMATION_SESSION_KEY, None) != adoption_id:
        return redirect(url_for("site.bench", bench_id=adoption.bench_id))

    return render_template(
        "adopt_confirmation.html",
        adoption=adoption,
        bench=adoption.bench,
        adoption_option=ADOPTION_OPTIONS[adoption.adoption_type],
    )
