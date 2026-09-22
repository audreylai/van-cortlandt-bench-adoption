import os

from dotenv import load_dotenv

load_dotenv()

# accomodate for psycopg3 connection string format
database_url = os.getenv("DATABASE_URL")
if database_url is None:
	raise RuntimeError("DATABASE_URL environment variable is not set.")

if database_url.startswith(("postgres://", "postgresql://")):
    database_url = database_url.replace("://", "+psycopg://", 1)


class Config:
    SQLALCHEMY_DATABASE_URI = database_url
    SQLALCHEMY_TRACK_MODIFICATIONS = False
