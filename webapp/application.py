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

    file_info = db.execute("SELECT * FROM user_uploads WHERE id = :userid ORDER BY date DESC", userid = userid)
    user_info = db.execute("SELECT bio, filename, full_name, username  FROM users WHERE id = :userid", userid = userid)
    bio = user_info[0]['bio']
    profile_picture = user_info[0]["filename"]
    full_name = user_info[0]["full_name"]
    username = user_info[0]["username"]
    file_name = user_info[0]["filename"]

    # counter for followers and following on the profile page of each users
    following_info = db.execute("SELECT following_username, following_full_name FROM volgend WHERE own_id = :userid",
                                userid = userid)
    followers_info = db.execute("SELECT own_username, own_full_name FROM volgend WHERE following_id = :userid", userid = userid)
    following_count = len(following_info)
    followers_count = len(followers_info)


    # for like and dislike button
    liked_filenames = liked_photos(userid)

    return render_template("index.html", full_name = full_name, username = username, file_info = file_info, bio=bio, \
                            profile_picture=profile_picture, following_count=following_count, followers_count=followers_count,
                            liked_filenames = liked_filenames)

@app.route("/profile", methods=["GET", "POST"])
@login_required
def profile():
    """Weergeeft een index van een andere gebruiker"""

    userid = session["user_id"]
    full_name = request.args.get('username')
    username = request.args.get('fullname')
    following_user = following_users(userid)

    user_info = db.execute("SELECT bio, filename, full_name, username, id  FROM users WHERE username=:username", username = username)
    id_username = user_info[0]["id"]
    bio = user_info[0]['bio']
    profile_picture = user_info[0]["filename"]

    # fullname and username of your followers and users you follow
    following_info = db.execute("SELECT following_username, following_full_name FROM volgend WHERE own_id = :own_id",
                                own_id= id_username)
    followers_info = db.execute("SELECT own_username, own_full_name FROM volgend WHERE following_id = :following_id",
                                following_id= id_username)

    # counter for followers and following on the profile page of each users
    following_count = len(following_info)
    followers_count = len(followers_info)

    user_profile = db.execute("SELECT * FROM user_uploads WHERE username=:username ORDER BY date DESC", username = username)

    # for like and dislike button
    liked_filenames = liked_photos(userid)

    return render_template("profile.html", username=username, full_name=full_name, bio = bio, user_profile = user_profile, \
                            profile_picture=profile_picture, following_count=following_count, followers_count=followers_count,
                            liked_filenames = liked_filenames, following_user=following_user)

@app.route("/login", methods=["GET", "POST"])
def login():
    """Log user in."""

    username = request.form.get("username")

    # forget any user_id
    session.clear()

    # if user reached route via POST (as by submitting a form via POST)
    if request.method == "POST":

        # ensure username was submitted
        if not username:
            return apology("must provide username")

        # ensure password was submitted
        elif not request.form.get("password"):
            return apology("must provide password")

        # query database for username
        rows = db.execute("SELECT * FROM users WHERE username = :username", username = username)

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

    full_name = request.form.get("full_name")
    username = request.form.get("username")
    password = request.form.get("password")
    password_control = request.form.get("password_control")

    # forget any user_id
    session.clear()

    # if user reached route via POST (as by submitting a form via POST)
    if request.method == "POST":

        # ensure password was submitted
        if not full_name:
            return apology("must provide full name")

        # ensure username was submitted
        elif not username:
            return apology("must provide username")

        # ensure password was submitted
        elif not password:
            return apology("must provide password")

        # ensure password control was submitted
        elif not password_control:
            return apology("must provide password control")

        # ensures password is the same as password control
        elif not password == password_control:
            return apology("Password control must be the same as password")

        # hashing the password
        hash = pwd_context.hash(password)

        # inserts the new user in to the users together with the hash of the password
        insert_username = db.execute("INSERT INTO users (username, hash, full_name) VALUES (:username, :hash, :full_name)",\
        username = username, hash = hash, full_name = full_name )

        # if username is already taken in users
        if not insert_username:
            return apology("Username has been taken")

        # query database for username
        rows = db.execute("SELECT * FROM users WHERE username = :username", username = username)

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
    userid = session["user_id"]

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
        get_hash = db.execute("SELECT hash FROM users WHERE id = :current_user", current_user = userid)

        # check if old password is correct
        if not pwd_context.verify((request.form.get("old_password")), get_hash[0]['hash']):
           return apology("old password is not correct")

        # update new password in users
        else:
            db.execute("UPDATE users SET hash = :new_hash WHERE  id = :current_user", new_hash = \
                        pwd_context.hash(request.form.get("new_password")), current_user = userid)

        return redirect(url_for("index"))

    # else if user reached route via GET (as by clicking a link or via redirect)
    else:
        return render_template("change_password.html")

@app.route("/followers", methods=["GET", "POST"])
@login_required
def followers():
    """Displays a list with all the followers of the user"""
    userid = session["user_id"]

    following_user = following_users(userid)

    # check if you are going to look at another profile's list of followers or your own list
    username = request.args.get('username')

    # if you are going to watch another profile's list get the data of that profile
    if username:
        id_username = get_id(username)
        followers = db.execute("SELECT own_username, own_full_name FROM volgend WHERE following_id = :following_id",
                                following_id = id_username)

    # get the data of your own profile
    else:
        followers = db.execute("SELECT own_username, own_full_name FROM volgend WHERE following_id = :userid", userid = userid)

    # print screen on page
    return render_template("followers.html", users = followers, following_user=following_user)

@app.route("/add_following", methods=["GET", "POST"])
@login_required
def add_following():
    """ Adds a user to your followers and/or following list"""
    userid = session["user_id"]

    # request the name of the person who you want to follow
    username = request.args.get('username')

    # acces the data of the user you want to follow in the database
    users = db.execute("SELECT full_name, username, id FROM users WHERE username = :username", username = username)
    following_full_name = users[0]["full_name"]
    following_username = users[0]["username"]
    # id from user who you want to follow
    following_id = users[0]["id"]

    # get the data of the user who wants to follow the person
    own_user = db.execute("SELECT full_name, username FROM users WHERE id = :userid", userid = userid)
    own_full_name = own_user[0]["full_name"]
    own_username = own_user[0]["username"]

    # check the database
    following = db.execute("SELECT * FROM volgend WHERE following_username = :following_username AND own_username = :own_username",
                         following_username = following_username, own_username = own_username)

    # if you don't follow the user add the user to your following list
    if len(following) == 0:
        db.execute("INSERT INTO volgend (own_username, following_username, own_id, following_id, own_full_name, following_full_name) \
                    VALUES(:own_username, :following_username, :own_id, :following_id, :own_full_name, :following_full_name)",
                    own_username = own_username , following_username = following_username , own_id = userid,
                    following_id = following_id, own_full_name = own_full_name , following_full_name = following_full_name )

    return redirect(url_for("following"))

@app.route("/following", methods=["GET", "POST"])
@login_required
def following():
    """Displays a list with all the users that you are following"""

    userid = session["user_id"]

    # check if you are going to look at another profile's list of following or your own list
    username = request.args.get('username')

    # another profile's list
    if username:
        id_username = get_id(username)
        following = db.execute("SELECT following_username, following_full_name FROM volgend WHERE own_id = :own_id",
                                own_id = id_username)

    # your own profile
    else:
        following = db.execute("SELECT following_username, following_full_name FROM volgend WHERE own_id = :userid",
                                userid = userid)



    # print screen on page
    return render_template("following.html", users = following)


@app.route("/uploaden", methods=["GET", "POST"])
@login_required
def uploaden():
    """Upload a picture to your profile"""
    userid = session["user_id"]

    if request.method == "POST":

        # select username from user table
        users = db.execute("SELECT username, full_name FROM users WHERE id = :userid", userid = userid)
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
            filename = "{}_{}{}".format(username, number_files, extension)
            file.save(os.path.join(path, filename))

            description = request.form.get("description")

            # put the directory in database
            db.execute("INSERT INTO user_uploads (username, id, directory, description, filename, filetype) VALUES (:username, \
                        :userid, :directory, :description, :filename, :filetype)", username = username, userid = userid, directory \
                        = os.path.join(username, filename), description = description, filename = filename, filetype = "notgif")

            return redirect(url_for("index"))
    else:
        return render_template("uploaden.html")

@app.route("/gif", methods=["GET", "POST"])
@login_required
def gif():
    """ Get GIF from database/giphy"""

    if request.method == "POST":
        api_instance = giphy_client.DefaultApi()
        # giphy public api key
        api_key = "dc6zaTOxFJmzC"

        # get the user search request
        q = request.form.get("search")
        limit = 25

        # list with al GIF's url
        gifs = []

        # ensure search query was submitted
        if not q:
            return apology("missing query")

        try:
            # Search Endpoint
            api_response = api_instance.gifs_search_get(api_key, q, limit=limit)

            # from the datafile extract the url of the gif
            for gif in api_response.data:
                 gif_url = gifs.append(gif.images.fixed_height.url)

        except ApiException as e:
            print("Exception when calling DefaultApi->gifs_search_get: %s\n" % e)

        return render_template("gif_display.html", gifs = gifs)

    else:
        return render_template("gif.html")

@app.route("/gif_uploaden", methods=["GET", "POST"])
@login_required
def gif_uploaden():
    """Upload GIF to your profile"""
    userid = session["user_id"]

    if request.method == "POST":
        # select username from user table
        users = db.execute("SELECT username, full_name FROM users WHERE id = :userid", userid = userid)
        username = users[0]["username"]

        url = request.args.get("url")
        description = request.form.get("description")

        db.execute("INSERT INTO user_uploads (username, id, directory, description, filename, filetype)  VALUES (:username, :userid, \
                    :directory, :description, :filename, :filetype)", username = username, userid = userid, directory = url, \
                    description = description, filename = url , filetype = "gif")

        return redirect(url_for("index"))
    else:
        return render_template("gif.html")

@app.route("/search", methods=["GET", "POST"])
@login_required
def search():
    """Weergeeft een tabel met alle gebruikers"""
    userid = session["user_id"]

    following_user = following_users(userid)

    if request.method == "POST":

        search_input = request.form.get("search_input")
        filter_users = db.execute("SELECT username, full_name FROM users WHERE id != :userid  AND username LIKE :search_input OR \
                                    full_name LIKE :search_input", userid = userid, search_input = search_input+"%")

         # print screen on page
        return render_template("search.html", users = filter_users, following_user=following_user)
    else:
        return render_template("search.html")


@app.route('/uploaden/<user>/<filename>')
def uploaded_file(user, filename):
    return send_from_directory(os.path.join(app.config['UPLOAD_FOLDER'], user), filename)

@app.route("/like", methods=["GET", "POST"])
@login_required
def like():

    userid = session["user_id"]

    # get the filename of the picture that you want to like
    filename = request.args.get('filename')

    # get the current page of the user to redirect to when the button is pushed
    current_page = (request.referrer)

    # check if user already has liked the picture
    check_likes = db.execute("SELECT like FROM likes WHERE own_id = :userid AND filename = :filename",
                            userid = userid, filename = filename)

    # needed for total number of likes on picture
    check_likes_filename = db.execute("SELECT likes from user_uploads WHERE filename = :filename",
                                        filename = filename)

    # if you haven't liked the photo already set the like to 1
    if len(check_likes) == 0:
        db.execute("INSERT INTO likes (own_id, filename, like) VALUES(:userid, :filename, :like)",
                    userid = userid, filename = filename, like = 1)

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
            db.execute("UPDATE likes SET like = :like + 1 WHERE own_id = :userid AND filename = :filename",
                    like = check_likes_user, userid = userid, filename = filename)

            total_likes = check_likes_filename[0]["likes"]
            db.execute("UPDATE user_uploads SET likes = :likes + 1 WHERE filename = :filename",
                    likes = total_likes, filename = filename)

    return redirect(current_page)

@app.route("/dislike", methods=["GET", "POST"])
@login_required
def dislike():

    userid = session["user_id"]
    # get the filename of the picture that you want to dislike
    filename = request.args.get('filename')

    # get the current page of the user to redirect to when the button is pushed
    current_page = (request.referrer)

    # check if you already have liked the picture
    check_likes = db.execute("SELECT like FROM likes WHERE own_id = :userid AND filename = :filename",
                            userid = userid, filename = filename)
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
            db.execute("UPDATE likes SET like = :like - 1  WHERE own_id = :userid AND filename = :filename",
                        userid = userid, filename = filename, like = check_likes_user)

            total_likes = check_likes_filename[0]["likes"]
            db.execute("UPDATE user_uploads SET likes = :likes - 1 WHERE filename = :filename",
                        likes = total_likes, filename = filename)

    return redirect(current_page)

@app.route("/timeline", methods=["GET", "POST"])
@login_required
def timeline():
    userid = session["user_id"]

    # get al information of that users's profile
    user_profile = db.execute("SELECT * FROM user_uploads WHERE id = :userid ORDER BY date DESC", userid = userid)
    user_info = db.execute("SELECT bio, filename, full_name, username  FROM users WHERE id = :userid", userid = userid)
    bio = user_info[0]['bio']
    profile_picture = user_info[0]["filename"]
    full_name = user_info[0]["full_name"]
    username = user_info[0]["username"]
    users = db.execute("SELECT username, full_name FROM users")

    # create dict for linking to that user on timeline and trending page
    userdict = {user["username"] : user["full_name"] for user in users}

    # counter for followers and following on the profile page of each users
    id_username = db.execute("SELECT id FROM users WHERE username = :username", username = username)
    id_username = id_username[0]["id"]
    following_info = db.execute("SELECT following_username, following_full_name FROM volgend WHERE own_id = :id", id= id_username)
    followers_info = db.execute("SELECT own_username, own_full_name FROM volgend WHERE following_id = :id", id= id_username)
    following_count = len(following_info)
    followers_count = len(followers_info)


    following_list = db.execute("SELECT following_id FROM volgend WHERE own_id = :userid", userid = userid)

    (test_ids)=[d['following_id'] for d in following_list]


    liked_filenames = liked_photos(userid)

    timeline_photos = db.execute("SELECT * FROM user_uploads WHERE id IN (:ids) ORDER BY date DESC", ids = test_ids)
    return render_template("timeline.html",full_name=full_name, username=username, timeline_photos=timeline_photos, bio=bio, \
                            profile_picture=profile_picture, following_count=following_count, followers_count=followers_count, \
                            users = userdict, liked_filenames = liked_filenames)


@app.route("/settings", methods=["GET", "POST"])
@login_required
def settings():
    return render_template("settings.html")


@app.route("/trending", methods=["GET", "POST"])
@login_required
def trending():
    userid = session["user_id"]

    # get al information of that users's profile
    user_profile = db.execute("SELECT * FROM user_uploads WHERE id = :userid ORDER BY date DESC", userid = userid)
    user_info = db.execute("SELECT bio, filename, full_name, username  FROM users WHERE id = :userid", userid = userid)
    bio = user_info[0]['bio']
    profile_picture = user_info[0]["filename"]
    full_name = user_info[0]["full_name"]
    username = user_info[0]["username"]
    users = db.execute("SELECT username, full_name FROM users")

    # create dict for linking to that user on timeline and trending page
    userdict = {user["username"] : user["full_name"] for user in users}

    # counter for followers and following on the profile page of each users
    id_username = db.execute("SELECT id FROM users WHERE username = :username", username = username)
    id_username = id_username[0]["id"]
    following_info = db.execute("SELECT following_username, following_full_name FROM volgend WHERE own_id = :id", id= id_username)
    followers_info = db.execute("SELECT own_username, own_full_name FROM volgend WHERE following_id = :id", id= id_username)
    following_count = len(following_info)
    followers_count = len(followers_info)


    trending_photos = db.execute("SELECT * FROM user_uploads ORDER BY likes DESC")

    # for like and dislike button
    liked_filenames = liked_photos(userid)

    return render_template("trending.html", full_name = full_name, username = username, trending_photos=trending_photos, bio=bio, \
                            profile_picture=profile_picture, following_count=following_count, followers_count=followers_count, \
                            users = userdict, liked_filenames = liked_filenames)


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

    userid = session["user_id"]

    if request.method == "POST":
        users = db.execute("SELECT username, full_name FROM users WHERE id = :userid", userid = userid)
        full_name = users[0]["full_name"]
        username = users[0]["username"]

        # select username from user table
        users = db.execute("SELECT username, full_name FROM users WHERE id = :userid", userid = userid)
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
            extension = os.path.splitext(file.filename)
            filename = "profilepic_{}_{}{}".format(username, number_files, extension)
            file.save(os.path.join(path, filename))

            # put the directory in database
            db.execute("UPDATE users SET profile_pic_directory = :new_profile_pic_directory, filename = :filename WHERE  id = :userid",\
                        new_profile_pic_directory = os.path.join(username, filename), filename = filename, userid = userid)

            return redirect(url_for("bio"))
    else:
        return render_template("profile_picture.html")

@app.route("/remove_following", methods=["GET", "POST"])
@login_required
def remove_following():
    userid = session["user_id"]

    following_username = request.args.get('username')

    remove_following = db.execute("DELETE FROM volgend WHERE own_id = :own_id AND following_username = :following_username", \
                                    own_id = userid, following_username = following_username )

    return redirect(url_for("following"))

@app.route("/bio", methods=["GET", "POST"])
@login_required
def bio():

    userid = session["user_id"]

    if request.method == "POST":
        bio = request.form.get("bio")
        if not request.form.get("bio"):
            return apology("must fill in a bio")

        else:
            db.execute("UPDATE users SET bio = :new_bio WHERE  id = :userid", new_bio = bio, userid = userid)

        return redirect(url_for("index"))
    else:
        return render_template("bio.html")

    return render_template("trending.html", full_name = full_name, username = username, trending_photos=trending_photos)


@app.route("/add_comment", methods=["GET", "POST"])
@login_required
def add_comment():

    if request.method == "POST":

        comment = request.form.get("add_comment")
        if not comment:
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

           # if len(selected_comments) == 0:
           #     return apology("no comments yet")


            username_photo = selected_comments[0]["username_photo"]

            # search for full name to get back to profile
            select_fullname= db.execute("SELECT full_name FROM users WHERE username = :username_photo ",
                                        username_photo = username_photo)
            full_name =  select_fullname[0]["full_name"]



        return redirect(url_for("show_comments", filename=filename))
        #return render_template("show_comments.html", selected_comments = selected_comments, username_photo = username_photo,
                                #filename = filename, full_name = full_name, filetype = filetype)
    else:
        return render_template("profile.html")

@app.route("/show_comments", methods=["GET", "POST"])
@login_required
def show_comments():

    filename = request.args.get("filename")

    filetype = db.execute("SELECT * FROM user_uploads WHERE filename = :filename", filename = filename)

    selected_comments = db.execute("SELECT * FROM comments WHERE filename = :filename ORDER BY date DESC", filename = filename)

    if len(selected_comments) == 0:
        return apology("no comments yet")


    username_photo = selected_comments[0]["username_photo"]

    # search for full name to get back to profile
    select_fullname= db.execute("SELECT full_name FROM users WHERE username = :username_photo ", username_photo = username_photo)
    full_name =  select_fullname[0]["full_name"]
    return render_template("show_comments.html", selected_comments = selected_comments, username_photo = username_photo,
                            filename = filename, full_name = full_name, filetype = filetype)
