import os

from cs50 import SQL
from flask import Flask, flash, redirect, render_template, request, session
from flask_session import Session
from tempfile import mkdtemp
from werkzeug.security import check_password_hash, generate_password_hash
from datetime import datetime, date, timedelta
from helpers import login_required, convert12, format_date


# Configure application
app = Flask(__name__)


# Configure session to use filesystem (instead of signed cookies)
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

# Configure CS50 Library to use SQLite database
db = SQL("sqlite:///final.db")


@app.after_request
def after_request(response):
    """Ensure responses aren't cached"""
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    response.headers["Expires"] = 0
    response.headers["Pragma"] = "no-cache"
    return response

@app.route("/")
@login_required
def calendar ():
    """Show events for the week"""

    # get today’s datetime
    today = datetime.date(datetime.now())

    # get today's day of week as an integer (Monday = 0, Sunday = 6)
    weekday = today.weekday()

    # Creating a dictionary
    keys = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]

    values = []
    for i in range(0 - weekday, 7 - weekday):
        date = today + timedelta(days = i)
        values.append(str(date))

    dates = {}
    for i in range(len(keys)):
        dates[keys[i]] = values[i]

    new_date = dates["Friday"]
    fri_events = db.execute("SELECT event_name, start, place FROM events WHERE date = ? ORDER BY start", new_date)

    return render_template("calendar.html", dates = dates, fri_events = fri_events)


@app.route("/login", methods=["GET", "POST"])
def login():
    """Log user in"""

    # Forget any user_id
    session.clear()

    # User reached route via POST (as by submitting a form via POST)
    if request.method == "POST":

        # Ensure username was submitted
        if not request.form.get("username"):
            return flash("must provide username", 403)

        # Ensure password was submitted
        elif not request.form.get("password"):
            return flash("must provide password", 403)

        # Query database for username
        rows = db.execute("SELECT * FROM users WHERE username = ?", request.form.get("username"))

        # Ensure username exists and password is correct
        if len(rows) != 1 or not check_password_hash(rows[0]["hash"], request.form.get("password")):
            return flash("invalid username and/or password", 403)

        # Remember which user has logged in
        session["user_id"] = rows[0]["id"]

        # Redirect user to home page
        return redirect("/")

    # User reached route via GET (as by clicking a link or via redirect)
    else:
        return render_template("login.html")


@app.route("/logout")
def logout():
    """Log user out"""

    # Forget any user_id
    session.clear()

    # Redirect user to login form
    return redirect("/")


@app.route("/register", methods=["GET", "POST"])
def register():
    """Register user"""

    # User reached route via POST (as by submitting a form via POST)
    if request.method == "POST":

        #find username, password, confirmation
        username = request.form.get("username")
        password = request.form.get("password")
        confirmation = request.form.get("confirmation")

        # Ensure username was submitted
        if not username:
            flash("must provide username", 400)
            return redirect("/register")

        # Ensure password was submitted
        elif not password or not confirmation:
            flash("must provide password", 400)
            return redirect("/register")

        #see if usernaame is already in users table
        user_exists = db.execute("SELECT username FROM users WHERE username = ?", (username))

        # Ensure username exists and password is correct
        if user_exists:
            flash("username already exists", 400)
            return redirect("/register")

        #ensure the passwords are both entered identically
        if confirmation != password:
            flash("passwords do not match", 400)
            return redirect("/register")

        # make new account
        new_password = generate_password_hash(password)
        db.execute("INSERT INTO users (username, hash) VALUES (?,?)", username, new_password)

        # Redirect user to home page
        return redirect("/login")

    else:
        return render_template("register.html")


@app.route("/events", methods=["GET", "POST"])
def events():

    if request.method == "GET":
        return render_template("events.html")

    #in order to add an event, need to put hte values in unique variables corresponding with the events database columns
    if request.method == "POST":
        event_name = request.form.get("event_name")
        org_name = request.form.get("org_name")
        event_type = request.form.get("event_type")
        date = request.form.get("date")
        new_date = format_date(date)
        start_time = request.form.get("time")
        place = request.form.get("location")
        user_id = db.execute("SELECT id FROM users WHERE id = ?", session["user_id"])[0]["id"]

        #if start time is incomplete or not finished, prompt the user to input a complete time
        if start_time == "":

            flash("please enter a time", 400)
            return redirect("/events")

        #insert the new data into the database events in its own row
        db.execute("INSERT INTO events (user_id, org_name, event_name, date, start, place, event_type) VALUES (?,?,?,?,?,?,?)", user_id, org_name, event_name, new_date, convert12(start_time), place, event_type)

    #redirect user to home page
    return redirect("/")

@app.route("/list")
@login_required
def list():
    """Show all entered events"""
    #pull everything from the purchases table and insert into list.html
    event = db.execute("SELECT * FROM events ORDER BY date, start")

    return render_template("list.html", event = event)

@app.route("/search", methods=["GET", "POST"])
@login_required
def search ():
    """Search for events by filtering different fields"""
    if request.method == "GET":
        av_orgs = db.execute("SELECT org_name FROM events GROUP BY org_name")
        av_dates = db.execute("SELECT date FROM events GROUP BY date ORDER BY date")
        av_types = db.execute("SELECT event_type FROM events GROUP BY event_type")

        return render_template("search.html", av_orgs = av_orgs, av_dates = av_dates, av_types = av_types)

    #if request.method == "POST":

    #results = db.execute("SELECT * FROM events WHERE(event_type, date, org_name), start")

    #return render_template("search_results.html", results = results)




