import hmac
from datetime import date
from functools import wraps

from flask import (
    Blueprint,
    current_app,
    redirect,
    render_template,
    request,
    session,
    url_for,
)

from . import db
from .api import ADOPTION_OPTIONS, current_adoption
from .models import Adoption, AdoptionRequest, Bench

admin = Blueprint("admin", __name__, url_prefix="/admin")


def admin_required(view):
    @wraps(view)
    def wrapped_view(*args, **kwargs):
        if not session.get("admin_authenticated"):
            return redirect(url_for("admin.login", next=request.path))
        return view(*args, **kwargs)

    return wrapped_view


def bench_row(bench):
    adoption = current_adoption(bench)
    return {
        "id": bench.bench_id,
        "code": bench.code,
        "zone": bench.location,
        "bench_type": bench.bench_type,
        "sponsor": adoption.adopter_name if adoption else None,
        "sponsor_email": adoption.adopter_email if adoption else None,
        "until": adoption.end_date.strftime("%b %Y") if adoption else None,
        "adoption_id": adoption.adoption_id if adoption else None,
    }


def next_bench_code():
    existing_codes = {bench.code for bench in Bench.query.with_entities(Bench.code).all()}
    candidate_number = 1
    while f"{candidate_number:04d}" in existing_codes:
        candidate_number += 1
    return f"{candidate_number:04d}"


@admin.get("/")
@admin_required
def index():
    all_benches = Bench.query.order_by(Bench.bench_id).all()
    adopted_benches = [bench_row(bench) for bench in all_benches if current_adoption(bench)]
    available_benches = [bench_row(bench) for bench in all_benches if not current_adoption(bench)]
    adoption_requests = AdoptionRequest.query.order_by(AdoptionRequest.request_id.asc()).all()
    return render_template(
        "admin_dashboard.html",
        admin_username=current_app.config.get("ADMIN_USERNAME"),
        bench_count=len(all_benches),
        adoption_count=Adoption.query.count(),
        adopted_benches=adopted_benches,
        available_benches=available_benches,
        zones=sorted({bench.location for bench in all_benches}),
        adoption_requests=adoption_requests,
        request_benches=sorted(
            {
                (adoption_request.bench_id, adoption_request.bench.code)
                for adoption_request in adoption_requests
                if adoption_request.bench
            },
            key=lambda item: item[1],
        ),
        request_zones=sorted(
            {
                adoption_request.bench.location
                if adoption_request.bench
                else "Parade Ground"
                for adoption_request in adoption_requests
            }
        ),
    )


@admin.route("/bench/<int:bench_id>", methods=["GET", "POST"])
@admin_required
def bench_view(bench_id):
    bench_record = db.get_or_404(Bench, bench_id)
    adoption = current_adoption(bench_record)
    error = None

    if request.method == "POST":
        if adoption is None:
            return "This bench has no active adoption to edit.", 404
        adopter_name = request.form.get("adopter_name", "").strip()
        adopter_email = request.form.get("adopter_email", "").strip()
        dedication = request.form.get("dedication", "").strip() or None
        show_name = request.form.get("show_name") == "on"
        start_date = request.form.get("start_date")
        end_date = request.form.get("end_date")
        try:
            parsed_start_date = date.fromisoformat(start_date)
            parsed_end_date = date.fromisoformat(end_date)
        except (TypeError, ValueError):
            error = "Start and end dates must be valid dates."
        else:
            if not adopter_name or not adopter_email:
                error = "Adopter name and email are required."
            elif dedication and len(dedication) > 150:
                error = "Dedication must be 150 characters or fewer."
            elif parsed_end_date < parsed_start_date:
                error = "End date must be on or after the start date."
            else:
                adoption.adopter_name = adopter_name
                adoption.adopter_email = adopter_email
                adoption.dedication = dedication
                adoption.show_name = show_name
                adoption.start_date = parsed_start_date
                adoption.end_date = parsed_end_date
                db.session.commit()
                return redirect(url_for("admin.bench_view", bench_id=bench_id))

    return render_template("admin_bench.html", bench=bench_record, adoption=adoption, error=error)


@admin.route("/requests/<int:request_id>", methods=["GET", "POST"])
@admin_required
def request_view(request_id):
    adoption_request = AdoptionRequest.query.get_or_404(request_id)
    error = None
    if request.method == "POST":
        adopter_name = request.form.get("adopter_name", "").strip()
        adopter_email = request.form.get("adopter_email", "").strip()
        dedication = request.form.get("dedication", "").strip() or None
        requested_location = "Parade Ground"
        if not adopter_name or not adopter_email:
            error = "Adopter name and email are required."
        elif dedication and len(dedication) > 150:
            error = "Dedication must be 150 characters or fewer."
        else:
            adoption_request.adopter_name = adopter_name
            adoption_request.adopter_email = adopter_email
            adoption_request.dedication = dedication
            adoption_request.requested_location = requested_location
            db.session.commit()
            return redirect(url_for("admin.request_view", request_id=request_id))

    return render_template("admin_request.html", adoption_request=adoption_request, error=error)


@admin.post("/requests/<int:request_id>/approve")
@admin_required
def approve_request(request_id):
    adoption_request = AdoptionRequest.query.get_or_404(request_id)
    delete_other_requests = request.form.get("delete_other_requests") == "on"
    if delete_other_requests and adoption_request.bench_id:
        AdoptionRequest.query.filter(
            AdoptionRequest.bench_id == adoption_request.bench_id,
            AdoptionRequest.request_id != adoption_request.request_id,
        ).delete(synchronize_session=False)

    bench = adoption_request.bench
    if adoption_request.adoption_type == "new_bench" and bench is None:
        bench = Bench(
            code=next_bench_code(), # TODO: for now, auto generates bench code, add functionality to allow admin edit
            location="Parade Ground",
            bench_type="Concrete base",
        )
        db.session.add(bench)
        db.session.flush()

    adoption = Adoption(
        bench_id=bench.bench_id if bench else None,
        adopter_name=adoption_request.adopter_name,
        adopter_email=adoption_request.adopter_email,
        adoption_type=adoption_request.adoption_type,
        dedication=adoption_request.dedication,
        requested_location=adoption_request.requested_location,
        show_name=adoption_request.show_name,
        start_date=adoption_request.start_date,
        end_date=adoption_request.end_date,
    )
    db.session.add(adoption)
    db.session.delete(adoption_request)
    db.session.commit()
    if adoption.bench_id:
        return redirect(url_for("admin.bench_view", bench_id=adoption.bench_id))
    return redirect(url_for("admin.index"))


@admin.post("/requests/<int:request_id>/delete")
@admin_required
def delete_request(request_id):
    adoption_request = AdoptionRequest.query.get_or_404(request_id)
    db.session.delete(adoption_request)
    db.session.commit()
    return redirect(url_for("admin.index"))


@admin.route("/login", methods=["GET", "POST"])
def login():
    if session.get("admin_authenticated"):
        return redirect(url_for("admin.index"))

    error = None
    if request.method == "POST":
        username = request.form.get("username", "")
        password = request.form.get("password", "")
        configured_username = current_app.config.get("ADMIN_USERNAME", "")
        configured_password = current_app.config.get("ADMIN_PASSWORD", "")
        if (
            configured_username
            and configured_password
            and hmac.compare_digest(username, configured_username)
            and hmac.compare_digest(password, configured_password)
        ):
            session.clear()
            session["admin_authenticated"] = True
            next_url = request.args.get("next")
            return redirect(
                next_url
                if next_url and next_url.startswith("/") and not next_url.startswith("//")
                else url_for("admin.index")
            )
        error = "Invalid username or password."

    return render_template("admin_login.html", error=error)


@admin.post("/logout")
def logout():
    session.clear()
    return redirect(url_for("admin.login"))
