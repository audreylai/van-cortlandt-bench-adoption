import os

from dotenv import load_dotenv

load_dotenv()

# accomodate for psycopg3 connection string format
database_url = os.getenv("DATABASE_URL")
if database_url is None:
	raise RuntimeError("DATABASE_URL environment variable is not set.")

if database_url.startswith(("postgres://", "postgresql://")):
    database_url = database_url.replace("://", "+psycopg://", 1)


# TODO: need to make production vs dev config
class Config:
    SQLALCHEMY_DATABASE_URI = database_url
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SECRET_KEY = os.getenv("SECRET_KEY")
    ADMIN_USERNAME = os.getenv("ADMIN_USERNAME", "admin")
    ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD", "")
    MAILGUN_API_KEY = os.getenv("MAILGUN_API_KEY")
    MAILGUN_DOMAIN = os.getenv("MAILGUN_DOMAIN")
    MAILGUN_FROM_EMAIL = os.getenv("MAILGUN_FROM_EMAIL")
    MAIL_FROM_NAME = os.getenv("MAIL_FROM_NAME")
    SITE_URL = os.getenv("SITE_URL", "http://localhost:5000")
