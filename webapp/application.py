from cs50 import SQL
from flask import Flask, flash, redirect, render_template, request, session, url_for
from flask_session import Session
from passlib.apps import custom_app_context as pwd_context
from tempfile import mkdtemp

# added for uploading files
import os
from werkzeug.utils import secure_filename
ALLOWED_EXTENSIONS = set(['jpg', 'jpeg', 'gif'])


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

    users = db.execute("SELECT username, full_name FROM users WHERE id = :id", id = session["user_id"])
    full_name = users[0]["full_name"]
    username = users[0]["username"]

    return render_template("index.html", full_name = full_name, username = username)



@app.route("/profile", methods=["GET", "POST"])
@login_required
def profile():
    """Weergeeft een index van een andere gebruiker"""
    username = request.args.get('username')
    full_name = request.args.get('fullname')

    print(username)
    print(full_name)
    # print screen on page
    return render_template("profile.html", username=username, full_name=full_name)





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

    # forget any user_id
    session.clear()

    # redirect user to login form
    return redirect(url_for("login"))

@app.route("/register", methods=["GET", "POST"])
def register():
    """Register user."""
    # forget any user_id
    session.clear()

    # if user reached route via POST (as by submitting a form via POST)
    if request.method == "POST":

        # ensure password was submitted
        if not request.form.get("full_name"):
            return apology("must provide full name")

        # ensure username was submitted
        elif not request.form.get("username"):
            return apology("must provide username")

        # ensure password was submitted
        elif not request.form.get("password"):
            return apology("must provide password")

        # ensure password control was submitted
        elif not request.form.get("password_control"):
            return apology("must provide password control")

        # ensures password is the same as password control
        elif not request.form.get("password") == request.form.get("password_control"):
            return apology("Password control must be the same as password")

        # hashing the password
        hash = pwd_context.hash(request.form.get("password"))

        # inserts the new user in to the users together with the hash of the password
        insert_username = db.execute("INSERT INTO users (username, hash, full_name) VALUES (:username, :hash, :full_name)",\
        username = request.form.get("username"), hash=hash, full_name = request.form.get("full_name") )

        # if username is already taken in users
        if not insert_username:
            return apology("Username has been taken")

        # query database for username
        rows = db.execute("SELECT * FROM users WHERE username = :username", username=request.form.get("username"))

        # remember which user has logged in
        session["user_id"] = rows[0]["id"]

        # redirect user to home page
        return redirect(url_for("index"))

    # else if user reached route via GET (as by clicking a link or via redirect)
    else:
        return render_template("register.html")


@app.route("/change_password", methods=["GET", "POST"])
@login_required
def change_password():
    """Allows user to change password"""
        # if user reached route via POST (as by submitting a form via POST)
    if request.method == "POST":

        # ensure old password was submitted
        if not request.form.get("old_password"):
            return apology("must fill in old password")

        # ensure new password was submitted
        elif not request.form.get("new_password"):
            return apology("must fill in new password")

        # ensure password control was submitted
        elif not request.form.get("password_control"):
            return apology("must fill in password control")

        # ensures new password is the same as password control
        elif not request.form.get("new_password") == request.form.get("password_control"):
            return apology("Password control must be the same as password")

        # get hash old password
        get_hash = db.execute("SELECT hash FROM users WHERE id = :current_user", current_user = session["user_id"])

        # check if old password is correct
        if not pwd_context.verify((request.form.get("old_password")), get_hash[0]['hash']):
           return apology("old password is not correct")

        # update new password in users
        else:
            db.execute("UPDATE users SET hash = :new_hash WHERE  id = :current_user",\
            new_hash = pwd_context.hash(request.form.get("new_password")), current_user = session["user_id"])

        return redirect(url_for("index"))

    # else if user reached route via GET (as by clicking a link or via redirect)
    else:
        return render_template("change_password.html")

#@app.route("/gebruikers", methods=["GET", "POST"])
#@login_required
#def gebruikers():
#    """Weergeeft een tabel met alle gebruikers"""
#    users = db.execute("SELECT username, full_name FROM users WHERE id != :id", id = session["user_id"])

     # print screen on page
#    return render_template("gebruikers.html", users = users )

@app.route("/volgers", methods=["GET", "POST"])
@login_required
def volgers():
    """Weergeeft een tabel met alle volgers van de gebruiker"""
    volgers = db.execute("SELECT username, full_name FROM volgers WHERE id != :id", id = session["user_id"])

    # print screen on page
    return render_template("volgers.html", users = volgers )

@app.route("/volgend", methods=["GET", "POST"])
@login_required
def volgend():
    """Weergeeft een tabel met alle gebruikers die de gebruiker volgt"""
    volgend = db.execute("SELECT username, full_name FROM volgend WHERE id != :id", id = session["user_id"])

    # print screen on page
    return render_template("volgend.html", users = volgend )


@app.route("/uploaden", methods=["GET", "POST"])
@login_required
def uploaden():

    if request.method == "POST":

        # select username from user table
        users = db.execute("SELECT username, full_name FROM users WHERE id = :id", id = session["user_id"])
        username = users[0]["username"]

        # check if the user already has his own file
        newpath = r'/home/ubuntu/workspace/WEBik/webapp/userfotos/{}'.format(username)
        if not os.path.exists(newpath):
            os.makedirs(newpath)

        # direction where the file should be placed
        UPLOAD_FOLDER = '/home/ubuntu/workspace/WEBik/webapp/userfotos/{}'.format(username)
        app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

        # check if the post request has the file part
        if 'file' not in request.files:
            flash('No file part')
            return redirect(request.url)
        file = request.files['file']

        # if user does not select file
        if file.filename == '':
            flash('No selected file')
            return redirect(request.url)

        # upload the new file and rename it
        if file and allowed_file(file.filename):

            # save old file in the users folder
            filename = secure_filename(file.filename)
            file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))

            # give the file the name of the usere and a number
            first_part, file_extension = os.path.splitext('/home/ubuntu/workspace/WEBik/webapp/userfotos/{}/{}'\
            .format(username, filename))
            onlyfiles = next(os.walk('/home/ubuntu/workspace/WEBik/webapp/userfotos/{}'.format(username)))[2]
            number_files = str(len(onlyfiles))
            new_name = username + number_files + file_extension
            new_name_directory = '/home/ubuntu/workspace/WEBik/webapp/userfotos/{}/{}'.format(username, new_name)
            rename = os.rename('/home/ubuntu/workspace/WEBik/webapp/userfotos/{}/{}'.format(username, filename),\
            new_name_directory)


            # put the directory in database
            db.execute("INSERT INTO user_uploads (username, id, directory) VALUES (:username, :id, :directory)", username = username, id = session["user_id"], directory = new_name_directory )



            return render_template("index.html")

    else:
        return render_template("uploaden.html")



@app.route("/search", methods=["GET", "POST"])
@login_required
def search():
    """Weergeeft een tabel met alle gebruikers"""
    if request.method == "POST":


        search_input = request.form.get("search_input")
        filter_users = db.execute("SELECT username, full_name FROM users WHERE id != :id AND username LIKE :search_input OR full_name LIKE :search_input", id = session["user_id"], search_input=search_input+"%")

         # print screen on page
        return render_template("search.html", users = filter_users)
    else:
        return render_template("search.html")
