from flask import Blueprint

site = Blueprint("site", __name__)


@site.get("/")
def index():
    return "Home page goes here"


@site.get("/bench/<int:bench_id>")
def bench(bench_id):
    return f"Bench {bench_id} page goes here"


@site.get("/bench/<int:bench_id>/adopt")
def adopt_bench(bench_id):
    return f"Adopt bench {bench_id} page goes here"
