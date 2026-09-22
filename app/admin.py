import hmac
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
from .models import Adoption, Bench

admin = Blueprint("admin", __name__, url_prefix="/admin")


def admin_required(view):
	@wraps(view)
	def wrapped_view(*args, **kwargs):
		if not session.get("admin_authenticated"):
			return redirect(url_for("admin.login", next=request.path))
		return view(*args, **kwargs)

	return wrapped_view


@admin.get("/")
@admin_required
def index():
	return render_template(
		"admin_dashboard.html",
		admin_username=current_app.config.get("ADMIN_USERNAME"),
		bench_count=Bench.query.count(),
		adoption_count=Adoption.query.count(),
		pending_adoptions=(
			Adoption.query.filter_by(approved=False)
			.order_by(Adoption.adoption_id.asc())
			.all()
		),
		recent_adoptions=(
			Adoption.query.order_by(Adoption.adoption_id.desc()).limit(5).all()
		),
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
	adoption.approved = True
	db.session.commit()
	return redirect(url_for("admin.index"))


@admin.post("/logout")
def logout():
	session.clear()
	return redirect(url_for("admin.login"))