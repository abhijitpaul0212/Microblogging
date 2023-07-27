import os
import datetime
import functools

from flask import (
    Flask,
    session,
    render_template,
    request,
    abort,
    flash,
    redirect,
    url_for
)

from pymongo import MongoClient
from dotenv import load_dotenv
from passlib.hash import pbkdf2_sha256

load_dotenv()

def create_app():
    app = Flask(__name__)
    app.secret_key = os.getenv("SECRET_KEY")

    client = MongoClient(os.getenv("MONGODB_URI"))
    app.db = client.microblog

    def login_required(route):
        @functools.wraps(route)
        def route_wrapper(*args, **kwargs):
            email = session.get("email")
            users = {user.get("email"): user.get("password") for user in app.db.users.find({})}
            if email not in users:
                return redirect(url_for("login"))
            return route(*args, **kwargs)
        return route_wrapper

    @app.route("/home", methods=["GET", "POST"])
    @login_required
    def home():
        entries_with_date = [(entry.get("email"), entry.get("content"), entry.get("date"), datetime.datetime.strptime(entry.get("date"), "%Y-%m-%d").strftime("%b %d")) for entry in app.db.entries.find({})]
        entries_with_date.reverse()
        return render_template("home.html", entries=entries_with_date, email=session.get("email"))

    @app.route('/', methods=["GET", "POST"])
    def login():
        email = ""
        if request.method == "POST":
            email = request.form.get("email")
            password = request.form.get("password")
            
            users = {user.get("email"): user.get("password") for user in app.db.users.find({})}
            
            # if email in users and users.get(email) == password:
            if email in users:
                if pbkdf2_sha256.verify(password, users.get(email)):
                    session["email"] = email
                    return redirect(url_for('profile'))
            flash("Incorrect e-mail or password.")
        return render_template('login.html', email=email)

    @app.route('/signup', methods=["GET", "POST"])
    def signup():
        if request.method == "POST":
            email = request.form.get("email")
            password = request.form.get("password")
            # Before saving, we need to check for uniqueness of user id
            users = {user.get("email"): user.get("password") for user in app.db.users.find({})}
            if email not in users:
                # saving users data
                app.db.users.insert_one({"email": email, "password":  pbkdf2_sha256.hash(password)})
                flash("Successfully signed up.")
                return redirect(url_for('login'))
            else:
                flash("Account already exists with this email address. Try another one!")
        return render_template("signup.html")

    @app.route("/profile", methods=["GET", "POST"])
    @login_required
    def profile():
        if request.method == "POST":
            entry_content = request.form.get("content")
            formatted_date = datetime.datetime.today().strftime("%Y-%m-%d")
            app.db.entries.insert_one({"email": session.get("email"), "content": entry_content, "date": formatted_date})
            return redirect(url_for('profile'))
        
        entries_with_date = [(entry.get("email"), entry.get("content"), entry.get("date"), datetime.datetime.strptime(entry.get("date"), "%Y-%m-%d").strftime("%b %d")) for entry in app.db.entries.find({'email': session.get("email")})]
        entries_with_date.reverse()
        return render_template("profile.html", entries=entries_with_date, email=session.get("email"))

    @app.route("/signout")
    def signout():
        if 'email' in session:  
            session.pop('email',None)  
            return redirect(url_for('login'))  
        else:  
            return '<p>user already logged out</p>'  
    return app
