"""Populate the database with sample Van Cortlandt Park bench data.

Run from the project root with ``python seed.py``.
"""

from datetime import date

from app import create_app, db
from app.models import Adoption, Bench


BENCHES = [
	{
		"code": "VCP-0142",
		"location": "Parade Ground",
		"bench_type": "World's Fair",
		"dedication": "In memory of John Doe",
		"adopter_name": "Maria Lopez",
		"adopter_email": "maria.lopez@example.com",
		"adoption_type": "bench_adoption",
		"start_date": date(2025, 1, 15),
		"end_date": date(2027, 1, 14),
	},
	{
		"code": "VCP-0087",
		"location": "Vault Hill",
		"bench_type": "Concrete base",
  		"dedication": "In memory of Jane Doe",
		"adopter_name": "James Chen",
		"adopter_email": "james.chen@example.com",
		"adoption_type": "bench_adoption",
		"start_date": date(2024, 9, 1),
		"end_date": date(2026, 8, 31),
	},
	{
		"code": "VCP-0216",
		"location": "Golf House",
		"bench_type": "Concrete base",
		"dedication": "In memory of Robert Brown",
		"adopter_name": "Ava Williams",
		"adopter_email": "ava.williams@example.com",
		"adoption_type": "bench_adoption",
		"start_date": date(2025, 3, 20),
		"end_date": date(2027, 3, 19),
	},
	{
		"code": "VCP-0304",
		"location": "Nature Center",
		"bench_type": "World's Fair",
	},
	{
		"code": "VCP-0411",
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
	code = f"VCP-{candidate_number:04d}"
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
						start_date=data["start_date"],
						end_date=data["end_date"],
						dedication=data["dedication"],
					)
				)

		db.session.commit()
		print(f"Seeded {len(BENCHES)} benches.")


if __name__ == "__main__":
	seed()
