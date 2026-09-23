import os
from datetime import date
from email.utils import formataddr

import requests
from dotenv import load_dotenv
from flask import current_app, render_template

load_dotenv()

MAILGUN_API_KEY = os.getenv("MAILGUN_API_KEY")
MAILGUN_FROM_ADDRESS = os.getenv("MAILGUN_FROM_EMAIL") or os.getenv("MAILGUN_FROM_ADDRESS")
MAIL_FROM_NAME = os.getenv("MAIL_FROM_NAME")
MAILGUN_SEND_FROM = formataddr((MAIL_FROM_NAME, MAILGUN_FROM_ADDRESS)) if MAIL_FROM_NAME else MAILGUN_FROM_ADDRESS


def _mailgun_domain():
    if MAILGUN_FROM_ADDRESS and "@" in MAILGUN_FROM_ADDRESS:
        return MAILGUN_FROM_ADDRESS.rsplit("@", 1)[1]
    raise RuntimeError("[MAIL] Invalid MAILGUN_FROM_EMAIL address")


def send_html_mail(recipients, subject, html_message):
    if not MAILGUN_API_KEY or not MAILGUN_SEND_FROM:
        print("[MAIL] Mailgun environment variables missing.")
        return False

    url = f"https://api.mailgun.net/v3/{_mailgun_domain()}/messages"
    try:
        response = requests.post(
            url,
            auth=("api", MAILGUN_API_KEY),
            data={
                "from": MAILGUN_SEND_FROM,
                "to": recipients,
                "subject": subject,
                "html": html_message,
            },
        )
        if response.status_code != 200:
            print(f"[MAIL] Mailgun error {response.status_code}: {response.text}")
            return False
        return True
    except Exception as error:
        print("[MAIL] Mail error:", error)
        return False


def _bench_context(bench, requested_location=None):
    if bench is None:
        return {
            "id": None,
            "code": "New bench installation",
            "zone": requested_location or "Parade Ground",
        }
    return {"id": bench.bench_id, "code": bench.code, "zone": bench.location}


def _render(template, **context):
    context["site_url"] = current_app.config.get("SITE_URL", "http://localhost:5000")
    return render_template(f"mail/{template}.html", **context)


def send_request_received(adoption_request):
    bench = _bench_context(adoption_request.bench, adoption_request.requested_location)
    return send_html_mail(
        adoption_request.adopter_email,
        "Your Van Cortlandt bench adoption request was received",
        _render(
            "receipt",
            name=adoption_request.adopter_name,
            bench=bench,
            term_months=120,
            request_id=adoption_request.request_id,
            dedication=adoption_request.plaque_text,
            in_memory_name=adoption_request.in_memory_name,
            submitted_on=adoption_request.requested_date.strftime("%B %-d, %Y"),
        ),
    )


def send_request_approved(adoption, bench, request_id=None):
    bench_data = _bench_context(bench, adoption.requested_location)
    return send_html_mail(
        adoption.adopter_email,
        "Your Van Cortlandt bench adoption was approved",
        _render(
            "approved",
            name=adoption.adopter_name,
            bench=bench_data,
            donor_name=adoption.adopter_name,
            request_id=request_id,
            dedication=adoption.plaque_text,
            in_memory_name=adoption.in_memory_name,
            start_date=adoption.start_date.strftime("%B %-d, %Y"),
            end_date=adoption.end_date.strftime("%B %-d, %Y"),
        ),
    )


def send_request_deleted(
    adopter_name, adopter_email, bench=None, reason=None, request_id=None
):
    bench_data = _bench_context(bench)
    reason = reason or "The request was not approved."
    return send_html_mail(
        adopter_email,
        "Update on your Van Cortlandt bench adoption request",
        _render(
            "removed",
            name=adopter_name,
            bench=bench_data,
            request_id=request_id,
            removed_on=date.today().strftime("%B %-d, %Y"),
            reason=reason,
        ),
    )
