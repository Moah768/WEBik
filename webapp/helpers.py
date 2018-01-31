import csv
import urllib.request
from cs50 import SQL

from flask import redirect, render_template, request, session
from functools import wraps
# configure CS50 Library to use SQLite database
db = SQL("sqlite:///webik.db")

#added for uploading images
# added for uploading files
import os
from werkzeug.utils import secure_filename
ALLOWED_EXTENSIONS = set(['jpg', 'jpeg', 'gif'])



def apology(message):
    """Shows error if somethings not working and the reason """
    return render_template("apology.html", message = message)




def login_required(f):
    """
    Decorate routes to require login.

    http://flask.pocoo.org/docs/0.12/patterns/viewdecorators/
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if session.get("user_id") is None:
            return redirect("/login")
        return f(*args, **kwargs)
    return decorated_function



def allowed_file(filename):
    """Checks if file is allowed"""
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


def liked_photos(userid):
    """Gives liked images/gifs"""
    filenames = db.execute("SELECT filename FROM likes WHERE own_id = :userid and like = 1", userid = userid)

    liked_filenames = [filename["filename"] for filename in filenames]

    return liked_filenames



def following_users(userid):
    """"Gives users that follow the current user"""
    following = db.execute("SELECT following_username FROM volgend WHERE own_id = :userid", userid = userid)
    following_users = [user["following_username"] for user in following]

    return following_users


def get_id(username):
    """ Gets current users id""""
    id_username = db.execute("SELECT id FROM users WHERE username = :username", username = username)
    id_username = id_username[0]["id"]

    return id_username