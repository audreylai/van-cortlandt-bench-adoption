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
from .models import Adoption, Bench

admin = Blueprint("admin", __name__, url_prefix="/admin")


def admin_required(view):
	@wraps(view)
	def wrapped_view(*args, **kwargs):
		if not session.get("admin_authenticated"):
			return redirect(url_for("admin.login", next=request.path))
		return view(*args, **kwargs)

	return wrapped_view


def admin_bench_row(bench):
	active_adoption = current_adoption(bench)
	pending_adoption = next(
		(adoption for adoption in reversed(bench.adoptions) if not adoption.approved),
		None,
	)
	adoption = active_adoption or pending_adoption

	if active_adoption:
		status = "adopted"
	elif pending_adoption:
		status = "pending"
	else:
		status = "available"

	return {
		"id": bench.bench_id,
		"code": bench.code,
		"zone": bench.location,
		"bench_type": bench.bench_type,
		"status": status,
		"sponsor": adoption.adopter_name if adoption else None,
		"until": adoption.end_date.strftime("%b %Y") if adoption else None,
		"adoption_id": adoption.adoption_id if adoption else None,
	}


@admin.get("/")
@admin_required
def index():
	benches = [
		admin_bench_row(bench)
		for bench in Bench.query.order_by(Bench.bench_id).all()
	]
	return render_template(
		"admin_dashboard.html",
		admin_username=current_app.config.get("ADMIN_USERNAME"),
		bench_count=Bench.query.count(),
		adoption_count=Adoption.query.count(),
		benches=benches,
		zones=sorted({bench["zone"] for bench in benches}),
	)


@admin.route("/bench/<int:bench_id>", methods=["GET", "POST"])
@admin_required
def bench_view(bench_id):
	bench_record = db.get_or_404(Bench, bench_id)
	adoption_id = request.values.get("adoption_id", type=int)
	if adoption_id:
		adoption = Adoption.query.filter_by(
			adoption_id=adoption_id, bench_id=bench_id
		).first_or_404()
	else:
		adoption = (
			Adoption.query.filter_by(bench_id=bench_id, approved=False)
			.order_by(Adoption.adoption_id.desc())
			.first()
			or (bench_record.adoptions[-1] if bench_record.adoptions else None)
		)

	error = None
	if request.method == "POST":
		if adoption is None:
			return "This bench has no adoption request to edit.", 404

		adopter_name = request.form.get("adopter_name", "").strip()
		adopter_email = request.form.get("adopter_email", "").strip()
		adoption_type = request.form.get("adoption_type")
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
			elif adoption_type not in ADOPTION_OPTIONS:
				error = "A valid adoption option is required."
			elif dedication and len(dedication) > 150:
				error = "Dedication must be 150 characters or fewer."
			elif parsed_end_date < parsed_start_date:
				error = "End date must be on or after the start date."
			else:
				adoption.adopter_name = adopter_name
				adoption.adopter_email = adopter_email
				adoption.adoption_type = adoption_type
				adoption.dedication = dedication
				adoption.show_name = show_name
				adoption.start_date = parsed_start_date
				adoption.end_date = parsed_end_date
				db.session.commit()
				return redirect(
					url_for(
						"admin.bench_view",
						bench_id=bench_id,
						adoption_id=adoption.adoption_id,
					)
				)

	return render_template(
		"admin_bench.html",
		bench=bench_record,
		adoption=adoption,
		error=error,
	)


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


@admin.post("/adoptions/<int:adoption_id>/approve")
@admin_required
def approve_adoption(adoption_id):
	adoption = Adoption.query.get_or_404(adoption_id)
	delete_other_requests = request.form.get("delete_other_requests") == "on"
	if delete_other_requests:
		Adoption.query.filter(
			Adoption.bench_id == adoption.bench_id,
			Adoption.adoption_id != adoption.adoption_id,
		).delete(synchronize_session=False)
	adoption.approved = True
	db.session.commit()
	return redirect(
		url_for(
			"admin.bench_view",
			bench_id=adoption.bench_id,
			adoption_id=adoption.adoption_id,
		)
	)


@admin.post("/adoptions/<int:adoption_id>/delete")
@admin_required
def delete_adoption(adoption_id):
	adoption = Adoption.query.get_or_404(adoption_id)
	bench_id = adoption.bench_id
	db.session.delete(adoption)
	db.session.commit()
	return redirect(url_for("admin.bench_view", bench_id=bench_id))


@admin.post("/logout")
def logout():
	session.clear()
	return redirect(url_for("admin.login"))