from datetime import date

from flask import Blueprint, redirect, render_template, request, session, url_for

from . import db
from .api import ADOPTION_OPTIONS, adoption_end_date, current_adoption
from .models import Adoption, AdoptionRequest, Bench

site = Blueprint("site", __name__)
CONFIRMATION_SESSION_KEY = "adoption_confirmation_id"


def view_bench(bench):
    adoption = next(
        (
            adoption
            for adoption in bench.adoptions
            if adoption.end_date >= date.today()
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
            plaque_text=adoption.plaque_text,
            in_memory_name=adoption.in_memory_name,
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


@site.get("/bench/adopt")
def adopt_bench():
    selected_bench_id = request.args.get("bench_id", type=int)
    requested_bench = (
        db.session.get(Bench, selected_bench_id) if selected_bench_id else None
    )
    benches = [
        bench
        for bench in Bench.query.order_by(Bench.bench_id).all()
        if current_adoption(bench) is None
    ]
    selected_bench = next(
        (bench for bench in benches if bench.bench_id == selected_bench_id),
        None,
    )
    return render_template(
        "adopt_bench.html",
        benches=benches,
        selected_bench_id=selected_bench.bench_id if selected_bench else None,
        requested_bench=requested_bench,
        requested_bench_adopted=requested_bench is not None
        and current_adoption(requested_bench) is not None,
    )


@site.get("/bench/<int:bench_id>/adopt")
def legacy_adopt_bench(bench_id):
    db.get_or_404(Bench, bench_id)
    return redirect(url_for("site.adopt_bench", bench_id=bench_id), code=308)


@site.post("/bench/adopt")
def submit_adoption():
    adoption_type = request.form.get("adoption_type")
    selected_bench_id = request.form.get("bench_id", type=int)
    bench_record = (
        db.get_or_404(Bench, selected_bench_id)
        if selected_bench_id
        else None
    )
    if adoption_type == "bench_adoption" and bench_record is None:
        return "Please select a bench to adopt.", 400
    if adoption_type == "bench_adoption" and current_adoption(bench_record):
        return "This bench is already adopted.", 409

    adopter_name = request.form.get("adopter_name")
    adopter_email = request.form.get("adopter_email")
    plaque_text = request.form.get("plaque_text") or None
    in_memory_name = request.form.get("in_memory_name") or None
    requested_location = "Parade Ground" if adoption_type == "new_bench" else None
    show_name = request.form.get("show_name") == "on"

	# basic form validation
    if not adopter_name or not adopter_email:
        return "Adopter name and email are required.", 400
    if adoption_type not in ADOPTION_OPTIONS:
        return "A valid adoption option is required.", 400

    adoption = AdoptionRequest(
        bench=bench_record,
        adopter_name=adopter_name,
        adopter_email=adopter_email,
        adoption_type=adoption_type,
        plaque_text=plaque_text,
        in_memory_name=in_memory_name,
        requested_location=requested_location,
        show_name=show_name,
        requested_date=date.today(),
        start_date=date.today(),
        end_date=adoption_end_date(date.today(), adoption_type),
    )
    db.session.add(adoption)
    db.session.commit()
    session[CONFIRMATION_SESSION_KEY] = adoption.request_id

    return redirect(
        url_for("site.adoption_confirmation", adoption_id=adoption.request_id),
        code=303,
    )


@site.get("/adoption/confirmation/<int:adoption_id>")
def adoption_confirmation(adoption_id):
    adoption = db.get_or_404(AdoptionRequest, adoption_id)
    if session.pop(CONFIRMATION_SESSION_KEY, None) != adoption_id:
        return (
            redirect(url_for("site.bench", bench_id=adoption.bench_id))
            if adoption.bench_id
            else redirect(url_for("site.adopt_bench"))
        )

    return render_template(
        "adopt_confirmation.html",
        adoption=adoption,
        bench=adoption.bench,
        adoption_option=ADOPTION_OPTIONS[adoption.adoption_type],
    )
