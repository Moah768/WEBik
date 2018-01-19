from cs50 import SQL
from flask import Flask, flash, redirect, render_template, request, session, url_for
from flask_session import Session
from passlib.apps import custom_app_context as pwd_context
from tempfile import mkdtemp

import datetime

from helpers import *

# configure application
app = Flask(__name__)

# ensure responses aren't cached
if app.config["DEBUG"]:
    @app.after_request
    def after_request(response):
        response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
        response.headers["Expires"] = 0
        response.headers["Pragma"] = "no-cache"
        return response

# configure session to use filesystem (instead of signed cookies)
app.config["SESSION_FILE_DIR"] = mkdtemp()
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

# configure CS50 Library to use SQLite database
db = SQL("sqlite:///webik.db")

@app.route("/")
@login_required
def index():
    return apology("dit werkt nog niet")


@app.route("/login", methods=["GET", "POST"])
def login():
    """Log user in."""

    # forget any user_id
    session.clear()

    # if user reached route via POST (as by submitting a form via POST)
    if request.method == "POST":

        # ensure username was submitted
        if not request.form.get("username"):
            return apology("must provide username")

        # ensure password was submitted
        elif not request.form.get("password"):
            return apology("must provide password")

        # query database for username
        rows = db.execute("SELECT * FROM users WHERE username = :username", username=request.form.get("username"))

        # ensure username exists and password is correct
        if len(rows) != 1 or not pwd_context.verify(request.form.get("password"), rows[0]["hash"]):
            return apology("invalid username and/or password")

        # remember which user has logged in
        session["user_id"] = rows[0]["id"]

        # redirect user to home page
        return redirect(url_for("index"))

    # if not POST then must be GET, render to login
    else:
        return render_template("login.html")

@app.route("/logout")
def logout():
    """Log user out."""


@app.route("/register", methods=["GET", "POST"])
def register():
    """Register user."""
    if request.method == "POST":
        if not request.form.get("username"):
            return apology("no username filled in")

        # ensure password was submitted
        elif not request.form.get("password"):
            return apology("no password filled in")
        # ensure password_confirmation was submitted
        elif not request.form.get("confirmPassword"):
            return apology("no password confirmation filled in")

        elif request.form.get("password") != request.form.get("confirmPassword"):
            return apology("password fields do not match")

        # encrypt password
        hash = pwd_context.encrypt(request.form.get("password"))

        # comment
        result = db.execute("INSERT INTO users (username, hash, full_name) VALUES(:username, :hash, :full_name)", username=request.form.get("username"),hash=hash, full_name=full_name)

        if not result:
            return apology("choose another username.")

        rows = db.execute("SELECT * FROM users WHERE username = :username", username=request.form.get("username"))

        session["user_id"] = rows[0]["id"]

        return redirect(url_for("index"))

    else:
        return render_template("register.html")


@app.route("/change_password", methods=["GET", "POST"])
@login_required
def change_password():
    """Allows user to change password"""



