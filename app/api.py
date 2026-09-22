from flask import Blueprint, jsonify

api = Blueprint("api", __name__, url_prefix="/api")

@api.get("/benches")
def benches():
    return jsonify(message="Bench API routes go here")


@api.get("/bench/<int:bench_id>")
def bench(bench_id):
    return jsonify(message=f"Bench {bench_id} API route goes here")


@api.post("/bench/<int:bench_id>/adopt")
def adopt_bench(bench_id):
    return jsonify(message=f"Adopt bench {bench_id} API route goes here"), 501
