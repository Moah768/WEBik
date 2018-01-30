from cs50 import SQL
from flask import Flask, flash, redirect, render_template, request, session, url_for, send_from_directory
from flask_session import Session
from passlib.apps import custom_app_context as pwd_context
from tempfile import mkdtemp


# added for uploading files
import os
from werkzeug.utils import secure_filename
ALLOWED_EXTENSIONS = set(['jpg', 'jpeg', 'gif'])


import datetime
import giphy_client
import urllib,json
from giphy_client.rest import ApiException
from pprint import pprint
from helpers import *
import json

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

# direction where the file should be placed
UPLOAD_FOLDER = 'userphotos/'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

Session(app)

# configure CS50 Library to use SQLite database
db = SQL("sqlite:///webik.db")

@app.route("/")
@login_required
def index():
    """ Displays the profile of the user that has logged in"""

    userid = session["user_id"]

    user_profile = db.execute("SELECT * FROM user_uploads WHERE id = :userid ORDER BY date DESC", userid = userid)
    user_info = db.execute("SELECT bio, filename, full_name, username  FROM users WHERE id = :userid", userid = userid)
    bio = user_info[0]['bio']
    profile_picture = user_info[0]["filename"]
    full_name = user_info[0]["full_name"]
    username = user_info[0]["username"]
    users = db.execute("SELECT username, full_name FROM users WHERE id = :id", id = session["user_id"])


    filename = db.execute("SELECT username FROM users WHERE id = :id", id = session["user_id"])

    file_info = db.execute("SElECT * FROM user_uploads WHERE id = :id ORDER BY date DESC", id = session["user_id"])

    return render_template("index.html", full_name = full_name, username = username, file_info = file_info, bio=bio, profile_picture=profile_picture)

@app.route("/profile", methods=["GET", "POST"])
@login_required
def profile():
    """Weergeeft een index van een andere gebruiker"""

    userid = session["user_id"]

    full_name = request.args.get('username')
    username = request.args.get('fullname')

    user_profile = db.execute("SELECT * FROM user_uploads WHERE username=:username ORDER BY date DESC", username = username)
    user_info = db.execute("SELECT bio, filename, full_name, username  FROM users WHERE username=:username", username = username)

    bio = user_info[0]['bio']
    profile_picture = user_info[0]["filename"]


    return render_template("profile.html", username=username, full_name=full_name, bio = bio, user_profile = user_profile, profile_picture=profile_picture)





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
        return redirect(url_for("timeline"))

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
        return redirect(url_for("profile_picture"))

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

@app.route("/followers", methods=["GET", "POST"])
@login_required
def followers():
    """Displays a list with all the followers of the user"""

    # check if you are going to look at another profile's list of followers or your own list
    username = request.args.get('username')

    # if you are going to watch another profile's list get the data of that profile
    if username:
        id_username = db.execute("SELECT id FROM users WHERE username = :username", username = username)
        id_username = id_username[0]["id"]
        followers = db.execute("SELECT own_username, own_full_name FROM volgend WHERE following_id = :id", id= id_username)

    # get the data of your own profile
    else:
        followers = db.execute("SELECT own_username, own_full_name FROM volgend WHERE following_id = :id", id=session["user_id"])

    # print screen on page
    return render_template("followers.html", users = followers )

@app.route("/add_following", methods=["GET", "POST"])
@login_required
def add_following():
    """ Adds a user to your followers and/or following list"""

    # request the name of the person who you want to follow
    username = request.args.get('username')

    # acces the data of the user you want to follow in the database
    users = db.execute("SELECT full_name, username, id FROM users WHERE username = :username", username = username)
    following_full_name = users[0]["full_name"]
    following_username = users[0]["username"]
    # id from user who you want to follow
    following_id = users[0]["id"]

    # get the data of the user who wants to follow the person
    own_user = db.execute("SELECT full_name, username FROM users WHERE id = :id", id = session["user_id"])
    own_full_name = own_user[0]["full_name"]
    own_username = own_user[0]["username"]

    # check the database
    following = db.execute("SELECT * FROM volgend WHERE following_username = :following_username AND own_username = :own_username",
                         following_username = following_username, own_username = own_username)

    # if you don't follow the user add the user to your following list
    if len(following) == 0:
        db.execute("INSERT INTO volgend (own_username, following_username, own_id, following_id, own_full_name, following_full_name) \
                    VALUES(:own_username, :following_username, :own_id, :following_id, :own_full_name, :following_full_name)",
                    own_username = own_username , following_username = following_username , own_id = session["user_id"],
                    following_id = following_id, own_full_name = own_full_name , following_full_name = following_full_name )


    return redirect(url_for("following"))

@app.route("/following", methods=["GET", "POST"])
@login_required
def following():
    """Displays a list with all the users that you are following"""

    # check if you are going to look at another profile's list of following or your own list
    username = request.args.get('username')

    # another profile's list
    if username:
        id_username = db.execute("SELECT id FROM users WHERE username = :username", username = username)
        id_username = id_username[0]["id"]
        following = db.execute("SELECT following_username, following_full_name FROM volgend WHERE own_id = :id", id= id_username)

    # your own profile
    else:
        following = db.execute("SELECT following_username, following_full_name FROM volgend WHERE own_id = :id", id = session["user_id"])

    # print screen on page
    return render_template("following.html", users = following )


@app.route("/uploaden", methods=["GET", "POST"])
@login_required
def uploaden():

    if request.method == "POST":

        # select username from user table
        users = db.execute("SELECT username, full_name FROM users WHERE id = :id", id = session["user_id"])
        username = users[0]["username"]

        # check if the user already has his own file
        newpath = os.path.join(UPLOAD_FOLDER, username)
        if not os.path.exists(newpath):
            os.makedirs(newpath)

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
            file.filename = secure_filename(file.filename)
            path = os.path.join(UPLOAD_FOLDER, username)
            number_files = len(next(os.walk(path))[2])
            _, extension = os.path.splitext(file.filename)
            filename = "{}{}{}".format(username, number_files, extension)
            file.save(os.path.join(path, filename))

            description = request.form.get("description")

            # put the directory in database
            db.execute("INSERT INTO user_uploads (username, id, directory, description, filename) \
                        VALUES (:username, :id, :directory, :description, :filename)", username = username, \
                        id = session["user_id"], directory = os.path.join(username, filename), description=description, filename=filename)








            return redirect(url_for("index"))
    else:
        return render_template("uploaden.html")

@app.route("/gif", methods=["GET", "POST"])
@login_required
def gif():

    if request.method == "POST":

        api_instance = giphy_client.DefaultApi()
        # giphy public api key
        api_key = "dc6zaTOxFJmzC"

        # get the user search request
        q = request.form.get("search")
        limit = 1

        # ensure search query was submitted
        if not q:
            return apology("missing query")

        try:
            # Search Endpoint
            api_response = api_instance.gifs_search_get(api_key, q, limit=limit)

            # from the datafile extract the url of the gif
            for gif in api_response.data:
                 gif_url = gif.embed_url


        except ApiException as e:
            print("Exception when calling DefaultApi->gifs_search_get: %s\n" % e)

        return render_template("gif_display.html", gif_url = gif_url)

    else:
        return render_template("gif.html")



@app.route("/search", methods=["GET", "POST"])
@login_required
def search():
    """Weergeeft een tabel met alle gebruikers"""

    if request.method == "POST":

        search_input = request.form.get("search_input")
        filter_users = db.execute("SELECT username, full_name FROM users WHERE id != :id \
                                    AND username LIKE :search_input OR full_name LIKE :search_input", \
                                    id = session["user_id"], search_input=search_input+"%")

         # print screen on page
        return render_template("search.html", users = filter_users)
    else:
        return render_template("search.html")


@app.route('/uploaden/<user>/<filename>')
def uploaded_file(user, filename):
    return send_from_directory(os.path.join(app.config['UPLOAD_FOLDER'], user), filename)



@app.route("/like", methods=["GET", "POST"])
@login_required
def like():
    # get the filename of the picture that you want to like
    filename = request.args.get('filename')

    # get the cuurent page of the user to redirect to when the button is pushed
    current_page = (request.referrer)

    # check if user already has liked the picture
    check_likes = db.execute("SELECT like FROM likes WHERE own_id = :id AND filename = :filename",
                            id = session["user_id"], filename = filename)

    # needed for total number of likes on picture
    check_likes_filename = db.execute("SELECT likes from user_uploads WHERE filename = :filename",
                                        filename = filename)

    # if you haven't liked the photo already set the like to 1
    if len(check_likes) == 0:
        db.execute("INSERT INTO likes (own_id, filename, like) VALUES(:id, :filename, :like)",
                    id = session["user_id"], filename = filename, like = 1)

        # get total number of likes
        total_likes = check_likes_filename[0]["likes"]
        db.execute("UPDATE user_uploads SET likes = :likes + 1 WHERE filename = :filename",
                    likes = total_likes, filename = filename)

    # if you already liked the picture
    else:
        check_likes_user = check_likes[0]["like"]
        if check_likes_user == 1:
            return apology("you already liked this picture")
        else:
            # update the number of likes in user_uploads and likes
            db.execute("UPDATE likes SET like = :like + 1 WHERE own_id = :id AND filename = :filename",
                    like = check_likes_user, id = session["user_id"], filename = filename)

            total_likes = check_likes_filename[0]["likes"]
            db.execute("UPDATE user_uploads SET likes = :likes + 1 WHERE filename = :filename",
                    likes = total_likes, filename = filename)

    return redirect(current_page)

@app.route("/dislike", methods=["GET", "POST"])
@login_required
def dislike():
    # get the filename of the picture that you want to dislike
    filename = request.args.get('filename')

    # get the cuurent page of the user to redirect to when the button is pushed
    current_page = (request.referrer)

    # check if you already have liked the picture
    check_likes = db.execute("SELECT like FROM likes WHERE own_id = :id AND filename = :filename",
                            id = session["user_id"], filename = filename)
    # needed for overall likes
    check_likes_filename = db.execute("SELECT likes from user_uploads WHERE filename = :filename",
                                        filename = filename)

    # check if the user has to like the picture first to create row in likes
    if len(check_likes) == 0:
        return apology("you have to like the picture first")

    else:
        # update the tables with new number of likes
        check_likes_user = check_likes[0]["like"]
        if check_likes_user == 0:
            return apology ("you have to like this picture first")

        else:
            db.execute("UPDATE likes SET like = :like - 1  WHERE own_id = :id AND filename = :filename",
                        id = session["user_id"], filename = filename, like = check_likes_user)

            total_likes = check_likes_filename[0]["likes"]
            db.execute("UPDATE user_uploads SET likes = :likes - 1 WHERE filename = :filename",
                        likes = total_likes, filename = filename)

    return redirect(current_page)

@app.route("/timeline", methods=["GET", "POST"])
@login_required
def timeline():
    userid = session["user_id"]

    user_profile = db.execute("SELECT * FROM user_uploads WHERE id = :userid ORDER BY date DESC", userid = userid)
    user_info = db.execute("SELECT bio, filename, full_name, username  FROM users WHERE id = :userid", userid = userid)
    bio = user_info[0]['bio']
    profile_picture = user_info[0]["filename"]
    full_name = user_info[0]["full_name"]
    username = user_info[0]["username"]
    users = db.execute("SELECT username, full_name FROM users WHERE id = :id", id = userid)


    following_list = db.execute("SELECT following_id FROM volgend WHERE own_id = :id", id = session["user_id"])

    (test_ids)=[d['following_id'] for d in following_list]

    timeline_photos = db.execute("SELECT * FROM user_uploads WHERE id IN (:ids) ORDER BY date DESC", ids = test_ids)
    return render_template("timeline.html",full_name=full_name, username=username, timeline_photos=timeline_photos, \
                            bio=bio, profile_picture=profile_picture)


@app.route("/settings", methods=["GET", "POST"])
@login_required
def settings():
    return render_template("settings.html")


@app.route("/trending", methods=["GET", "POST"])
@login_required
def trending():
    userid = session["user_id"]

    user_profile = db.execute("SELECT * FROM user_uploads WHERE id = :userid ORDER BY date DESC", userid = userid)
    user_info = db.execute("SELECT bio, filename, full_name, username  FROM users WHERE id = :userid", userid = userid)

    bio = user_info[0]['bio']
    profile_picture = user_info[0]["filename"]
    full_name = user_info[0]["full_name"]
    username = user_info[0]["username"]
    users = db.execute("SELECT username, full_name FROM users WHERE id = :id", id = userid)

    trending_photos = db.execute("SELECT * FROM user_uploads ORDER BY likes DESC")

    return render_template("trending.html", full_name = full_name, username = username, \
                            trending_photos=trending_photos, bio=bio, profile_picture=profile_picture)


@app.route("/delete", methods=["GET", "POST"])
@login_required
def delete():
    # get name of file you want to delete
    delete_name = request.args.get('filename')

    # delete file in database
    delete_photo = db.execute("DELETE FROM user_uploads WHERE filename = :filename",filename = delete_name)

    return redirect(url_for("index"))

@app.route("/profile_picture", methods=["GET", "POST"])
@login_required
def profile_picture():

    if request.method == "POST":
        users = db.execute("SELECT username, full_name FROM users WHERE id = :id", id = session["user_id"])
        full_name = users[0]["full_name"]
        username = users[0]["username"]

        # select username from user table
        users = db.execute("SELECT username, full_name FROM users WHERE id = :id", id = session["user_id"])
        username = users[0]["username"]

        # check if the user already has his own file
        newpath = os.path.join(UPLOAD_FOLDER, username)
        if not os.path.exists(newpath):
            os.makedirs(newpath)

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
            file.filename = secure_filename(file.filename)
            path = os.path.join(UPLOAD_FOLDER, username)
            number_files = len(next(os.walk(path))[2])
            _, extension = os.path.splitext(file.filename)
            filename = "profilepic_{}{}{}".format(username, number_files, extension)
            file.save(os.path.join(path, filename))

            # put the directory in database
            db.execute("UPDATE users SET profile_pic_directory = :new_profile_pic_directory, filename = :filename WHERE  id = :id", new_profile_pic_directory = os.path.join(username, filename), filename = filename, id = session["user_id"])

            return redirect(url_for("bio"))
    else:
        return render_template("profile_picture.html")

@app.route("/remove_following", methods=["GET", "POST"])
@login_required
def remove_following():

    following_username = request.args.get('username')

    remove_following = db.execute("DELETE FROM volgend WHERE own_id = :own_id AND following_username = :following_username", own_id = session["user_id"], following_username = following_username )

    return redirect(url_for("following"))

@app.route("/bio", methods=["GET", "POST"])
@login_required
def bio():
    if request.method == "POST":
        bio = request.form.get("bio")
        if not request.form.get("bio"):
            return apology("must fill in a bio")

        else:
            db.execute("UPDATE users SET bio = :new_bio WHERE  id = :userid", new_bio = bio, userid = session["user_id"])

        return redirect(url_for("index"))
    else:
        return render_template("bio.html")

    return render_template("trending.html", full_name = full_name, username = username, trending_photos=trending_photos)


@app.route("/add_comment", methods=["GET", "POST"])
@login_required
def add_comment():
    if request.method == "POST":
        comment = request.form.get("add_comment")
        if not request.form.get("add_comment"):
            return apology("must fill in a comment")

        else:
            filename = request.args.get("filename")
            username_photo = request.args.get("username")

            userid = session["user_id"]
            user_profile = db.execute("SELECT * FROM users WHERE id = :userid", userid = userid)
            own_username = user_profile[0]["username"]

            db.execute("INSERT INTO comments (own_username, username_photo, filename, comment) VALUES (:own_username, :username_photo, :filename, :comment)",\
            own_username = own_username, username_photo = username_photo,  filename = filename, comment = comment)

        selected_comments = db.execute("SELECT * FROM comments WHERE filename = :filename ORDER BY date DESC", filename = filename)

        return render_template("show_comments.html", selected_comments = selected_comments )
    else:
        return render_template("add_comment.html")

@app.route("/show_comments", methods=["GET", "POST"])
@login_required
def show_comments():
    filename = request.args.get("filename")
    selected_comments = db.execute("SELECT * FROM comments WHERE filename = :filename ORDER BY date DESC", filename = filename)

    return render_template("show_comments.html", selected_comments = selected_comments )
