"""
FOR DEVELOPMENT PURPOSES ONLY. Do not use in production. A more advanced data import/export tool should be used for production data management.
Populate the database with sample Van Cortlandt Park bench data. 


Run from the project root with ``python seed.py``.

"""

from datetime import date

from app import create_app, db
from app.api import adoption_end_date
from app.models import Adoption, AdoptionRequest, Bench


BENCHES = [
	{
		"code": "0142",
		"location": "Parade Ground",
		"bench_type": "World's Fair",
		"plaque_text": "Forever in our hearts",
		"in_memory_name": "John Doe",
		"adopter_name": "Maria Lopez",
		"adopter_email": "maria.lopez@example.com",
		"adoption_type": "bench_adoption",
		"start_date": date(2026, 1, 15),
	},
	{
		"code": "0087",
		"location": "Vault Hill",
		"bench_type": "Concrete base",
		"plaque_text": "With love and gratitude",
		"in_memory_name": "Jane Doe",
		"adopter_name": "James Chen",
		"adopter_email": "james.chen@example.com",
		"adoption_type": "bench_adoption",
		"start_date": date(2026, 2, 1),
	},
	{
		"code": "0216",
		"location": "Golf House",
		"bench_type": "Concrete base",
		"plaque_text": "A lasting remembrance",
		"in_memory_name": "Robert Brown",
		"adopter_name": "Ava Williams",
		"adopter_email": "ava.williams@example.com",
		"adoption_type": "bench_adoption",
		"start_date": date(2026, 3, 20),
	},
	{
		"code": "0304",
		"location": "Nature Center",
		"bench_type": "World's Fair",
	},
	{
		"code": "0411",
		"location": "Croton Woods",
		"bench_type": "Concrete base",
	},
]

LOCATIONS = [
	"Van Cortlandt Lake",
	"Golf Course",
	"Parade Ground",
	"Van Cortlandt House Museum",
	"Van Cortlandt Stadium",
	"Tibbetts Brook",
	"Ecology Center",
	"Croton Woods",
]

existing_codes = {bench["code"] for bench in BENCHES}
candidate_number = 1
while len(BENCHES) < 500:
	code = f"{candidate_number:04d}"
	candidate_number += 1
	if code in existing_codes:
		continue
	existing_codes.add(code)
	BENCHES.append(
		{
			"code": code,
			"location": LOCATIONS[(len(BENCHES) - 5) % len(LOCATIONS)],
			"bench_type": "World's Fair" if len(BENCHES) % 2 else "Concrete base",
		}
	)


def seed() -> None:
	"""Insert the sample records, replacing any previous sample data."""
	app = create_app()
	with app.app_context():
		db.create_all()
		db.session.query(AdoptionRequest).delete()
		db.session.query(Adoption).delete()
		db.session.query(Bench).delete()

		for data in BENCHES:
			bench = Bench(
				code=data["code"],
				location=data["location"],
				bench_type=data["bench_type"],
			)
			db.session.add(bench)

			if "adopter_name" in data:
				bench.adoptions.append(
					Adoption(
						adopter_name=data["adopter_name"],
						adopter_email=data["adopter_email"],
						adoption_type=data["adoption_type"],
						plaque_text=data.get("plaque_text"),
						in_memory_name=data.get("in_memory_name"),
						start_date=data["start_date"],
						end_date=adoption_end_date(data["start_date"], data["adoption_type"]),
					)
				)

		db.session.commit()

		# Add 200 pending requests, including duplicate requests for the same benches.
		seeded_benches = Bench.query.order_by(Bench.bench_id).all()
		request_date = date(2026, 9, 22)
		request_number = 1

		for duplicate_group in range(90):
			bench = seeded_benches[duplicate_group + 5]
			for duplicate_number in range(2):
				adopter_name = f"Sample Adopter {request_number:03d}"
				adoption_type = "bench_adoption"
				db.session.add(
					AdoptionRequest(
						bench=bench,
						adopter_name=adopter_name,
						adopter_email=f"adopter{request_number:03d}@example.com",
						adoption_type=adoption_type,
						dedication=f"In honor of {adopter_name}",
						show_name=request_number % 4 != 0,
						requested_date=request_date,
						start_date=request_date,
						end_date=adoption_end_date(request_date, adoption_type),
					)
				)
				request_number += 1

		for new_bench_number in range(20):
			adoption_type = "new_bench"
			db.session.add(
				AdoptionRequest(
					adopter_name=f"New Bench Sponsor {new_bench_number + 1:02d}",
					adopter_email=f"newbench{new_bench_number + 1:02d}@example.com",
					adoption_type=adoption_type,
					dedication="A new place to rest in Van Cortlandt Park",
					requested_location="Parade Ground",
					show_name=True,
					requested_date=request_date,
					start_date=request_date,
					end_date=adoption_end_date(request_date, adoption_type),
				)
			)

		db.session.commit()
		print(f"Seeded {len(BENCHES)} benches and {request_number + 19} adoption requests.")


if __name__ == "__main__":
	seed()
