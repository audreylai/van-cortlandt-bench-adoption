from flask import Blueprint

auth = Blueprint("auth", __name__, url_prefix="/auth")


@auth.get("/login")
def login():
    return "Login page goes here"


@auth.get("/logout")
def logout():
    return "Logout route goes here"
