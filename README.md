# Van Cortlandt Bench Adoption

A Flask application for browsing Van Cortlandt Park benches, submitting adoption requests, and managing requests through an authenticated admin dashboard.

## Features
### Public user
- Browse all benches and see whether each is available or actively adopted.
- Search and filter the public bench directory by code, zone, and status.
- Submit a request to adopt an existing bench.
- Submit a request for a new bench installation in Parade Ground.

### Admin
- Hold requests for admin review before they become active adoptions.
- Manage active adoptions and pending requests from the admin dashboard.
- Approve or delete requests, including duplicate requests for the same bench.
- Automatically create a new bench record when a new-bench request is approved.
- Send Mailgun email confirmations when requests are received, approved, or deleted.

## Pages

### Public pages

| URL | Description |
| --- | --- |
| `/` | Homepage, map placeholder, and searchable bench directory. |
| `/bench/<bench_id>` | Public detail page for one bench. Pending requests are not shown. |
| `/bench/adopt` | Adoption request form for an existing bench or a new bench. |
| `/adoption/confirmation/<adoption_id>` | One-time confirmation page shown immediately after submitting a request. The value is the request ID in the current implementation. |

New-bench requests are assigned to Parade Ground when approved. The existing bench selector is hidden when the new-bench option is selected.

## Admin pages

Admin routes are protected by the configured username and password.

| URL | Description |
| --- | --- |
| `/admin/login` | Admin login page. Authenticated admins are redirected to the dashboard. |
| `/admin/` | Dashboard with adopted/available bench tabs and the adoption requests table. |
| `/admin/bench/<bench_id>` | Edit an active adoption for a bench, including its term dates. |
| `/admin/adoptions/<adoption_id>/delete` | Delete an active adoption and notify the adopter. |
| `/admin/requests/<request_id>` | Review and edit a pending adoption request. |
| `/admin/requests/<request_id>/approve` | Approve a request. New-bench requests create a bench automatically. |
| `/admin/requests/<request_id>/delete` | Delete a pending request. |
| `/admin/logout` | End the admin session. |

The dashboard supports bench search, zone filtering, pagination, request search, adoption-type filtering, request-zone filtering, and request pagination.

## API

All API endpoints return JSON.

### `GET /api/benches`

Returns all benches with their availability and active adoption details.

### `GET /api/bench/<bench_id>`

Returns one bench by its numeric database ID.

### `POST /api/bench/<bench_id>/adopt`

Creates a pending adoption request for an existing bench.

Example JSON body:

```json
{
  "adopter_name": "Jane Doe",
  "adopter_email": "jane@example.com",
  "adoption_type": "bench_adoption",
  "plaque_text": "In memory of John Doe",
  "show_name": true
}
```

The API does not accept new-bench requests. Use the public `/bench/adopt` form for those.

## Data model

- `Bench`: numeric bench code, location, and bench type.
- `AdoptionRequest`: pending request awaiting admin action. Includes adopter details, requested date, plaque text, and optional bench association.
- `Adoption`: approved active adoption associated with a bench.

Adoptions use a ten-year term ending one day before the ten-year anniversary of the start date.

## Local setup

Requirements: Python 3.10+ and PostgreSQL.

1. Create and activate a virtual environment:

	```bash
	python3 -m venv venv
	source venv/bin/activate
	```

2. Install dependencies:

	```bash
	pip install -r requirements.txt
	```

3. Create a `.env` file:

	```env
	DATABASE_URL=postgresql://username:password@localhost:5432/bench_adoption
	SECRET_KEY=replace-with-a-long-random-value
	ADMIN_USERNAME=admin
	ADMIN_PASSWORD=replace-with-a-secure-password
	MAILGUN_API_KEY=key-your-mailgun-api-key
	MAILGUN_DOMAIN=mg.example.com
	MAIL_FROM_NAME=Van Cortlandt Park
	MAILGUN_FROM_EMAIL=noreply@mg.example.com
	SITE_URL=http://localhost:5000
	```

4. Start the development server:

	```bash
	flask run
	```

The app creates missing tables during startup. Existing database changes are handled by the lightweight startup migrations in the app factory.

## Seed data

To reset the configured database with 500 benches, sample active adoptions, and 200 pending adoption requests:

```bash
python seed.py
```

The seed script deletes existing benches, active adoptions, and adoption requests before inserting sample data. Do not run it against a production database containing data you need to keep.

## Deploy on Render

1. Push the repository to GitHub.
2. In Render, create a **PostgreSQL** database.
3. Create a **Web Service** connected to the repository.
4. Configure:

	```text
	Build Command: pip install -r requirements.txt
	Start Command: gunicorn wsgi:app
	```

5. Add these environment variables to the Render web service:

	```env
	DATABASE_URL=<Render PostgreSQL Internal Database URL>
	SECRET_KEY=<long random production secret>
	ADMIN_USERNAME=<admin username>
	ADMIN_PASSWORD=<strong admin password>
	MAILGUN_API_KEY=<Mailgun API key>
	MAILGUN_DOMAIN=<Mailgun sending domain>
	MAIL_FROM_NAME=<sender display name>
	MAILGUN_FROM_EMAIL=<verified Mailgun sender address>
	SITE_URL=https://your-production-domain.example.com
	```

6. Deploy the service. Tables are created during application startup.
7. For a demo database, open the Render service **Shell** and run (note that shell is only available for paid Render subscriptions, just run locally and change your .env DATABASE_URL): 

	```bash
	python seed.py
	```

Run the seed command only once on a new database unless you intentionally want to erase and recreate the data.

## Future development plans

- Add a real interactive park map and bench coordinate
- Add CSRF protection and stronger production session/security settings
- Add email notifications for request submission, approval, and deletion using mailgun
- Add payment processing for adoption fees
- Add image uploads for individual benches, need cloud storage
- Add admin tools for editing bench metadata and managing locations
- Add audit history for request approvals, edits, and deletions
- Create tests for public pages, API validation, admin workflows, and database migrations