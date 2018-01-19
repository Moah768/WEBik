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

# custom filter
app.jinja_env.filters["usd"] = usd

# configure session to use filesystem (instead of signed cookies)
app.config["SESSION_FILE_DIR"] = mkdtemp()
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

# configure CS50 Library to use SQLite database
db = SQL("sqlite:///finance.db")

@app.route("/")
@login_required
def index():
    portfolio_info = db.execute("SELECT stock, shares FROM portfolio WHERE userid = :current_user", current_user = session["user_id"])

    cash_shares = 0

    # update the prices for every stock
    for info in portfolio_info:
        symbol = info["stock"]
        shares = info["shares"]
        stock = lookup(symbol)
        current_price = stock['price']
        total_value = shares * stock['price']
        cash_shares += total_value
        update_price = db.execute("UPDATE portfolio SET current_price = :current_price, total_value = :total_value WHERE userid = :current_user AND stock = :symbol", \
                    current_price = usd(current_price) , total_value = usd(total_value), current_user = session["user_id"], symbol = symbol)

    # amount of users current cash
    current_cash = db.execute("SELECT cash FROM users WHERE id = :current_user", current_user = session["user_id"])
    current_cash = int(current_cash[0]['cash'])

    # amount of users current cash + cash value of shares
    total_cash = cash_shares + current_cash

    # update portfolio for the use in index.html
    portfolio_update = db.execute("SELECT * from portfolio WHERE userid = :current_user", current_user = session["user_id"])
    return render_template("index.html", stocks = portfolio_update, current_cash = usd(current_cash), total_cash = usd(total_cash))


@app.route("/buy", methods=["GET", "POST"])
@login_required
def buy():
    """Buy shares of stock."""

    # if user reached route via POST (as by submitting a form via POST)
    if request.method == "POST":

        shares = int(request.form.get("number_shares"))

        # ensure stock symbol is submitted
        if not request.form.get("stock-symbol"):
            return apology("must fill in stock symbol")

        # ensure number of shares is submitted
        elif not request.form.get("number_shares"):
            return apology("must fill in number of shares")

        # ensure number of shares is bigger than zero
        elif shares <= 0:
            return apology("number of shares must be bigger than zero")

        # checks if stock symbol is valid
        stock_quote = lookup(request.form.get("stock-symbol"))
        if not stock_quote:
            return apology("stock isn't valid")

        # checks the current amount available cash of the user
        current_cash = db.execute("SELECT cash FROM users WHERE id = :current_user", current_user = session["user_id"])
        current_cash = int(current_cash[0]['cash'])

        # checks if user can afford the shares
        if current_cash < shares * stock_quote['price']:
            return apology("not enough cash")

        #update transactions with the shares the user bought
        transactions = db.execute("INSERT INTO transactions (userid, stock, price, shares, date) VALUES (:userid, :stock, :price, :shares, :date)",\
        userid = session["user_id"] , stock = stock_quote['symbol'], price = stock_quote['price'], shares = shares, date =  datetime.datetime.now())

        # update the current amount of cash the user has
        update_current_cash = db.execute("UPDATE users SET cash=cash-:spended_cash  WHERE id = :userid", spended_cash = (shares * stock_quote['price']),\
        userid =  session["user_id"])

        # check if shares are aleready in portfolio
        check_portfolio = db.execute("SELECT shares FROM portfolio WHERE userid = :current_user AND stock = :stock" , current_user = session["user_id"], stock = stock_quote['symbol'])

        # if stocks not yet in portfolio
        if not check_portfolio:
            add_portfolio = db.execute("INSERT INTO portfolio (userid, stock, shares, current_price, total_value) VALUES\
            (:userid,:stock, :shares, :current_price,:total_value)", userid = session["user_id"], stock = stock_quote['symbol'], shares = shares, current_price = stock_quote['price'], total_value = (shares * stock_quote['price']))

        # if already in portfolio add up shares
        else:
            update_shares = check_portfolio[0]['shares'] + shares
            update_total_value = update_shares * stock_quote['price']
            db.execute("UPDATE portfolio SET shares = :shares, total_value = :total_value WHERE userid = :userid AND stock = :stock",
            shares = update_shares, userid =  session["user_id"], total_value = usd(update_total_value), stock = stock_quote['symbol'])


        return redirect(url_for("index"))

    # else if user reached route via GET (as by clicking a link or via redirect)
    else:
        return render_template("buy.html")


@app.route("/history")
@login_required
def history():
    """Show history of transactions."""
    history = db.execute("SELECT * from transactions WHERE userid = :current_user", current_user = session["user_id"])

    return render_template("history.html", history = history)


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

    # else if user reached route via GET (as by clicking a link or via redirect)
    else:
        return render_template("login.html")

@app.route("/logout")
def logout():
    """Log user out."""

    # forget any user_id
    session.clear()

    # redirect user to login form
    return redirect(url_for("login"))

@app.route("/quote", methods=["GET", "POST"])
@login_required
def quote():
    """Get stock quote."""
    # if user reached route via POST (as by submitting a form via POST)
    if request.method == "POST":

        # retrieve stock information
        stock_quote = lookup(request.form.get("stock-symbol"))

        # if stock isn't valid
        if not stock_quote:
            return apology("Stock isn't valid")

        # returns form with requested stock info
        else:
         return render_template("quoted.html", stock_quote = stock_quote )

    # else if user reached route via GET (as by clicking a link or via redirect)
    else:
        return render_template("quote.html")

@app.route("/register", methods=["GET", "POST"])
def register():
    """Register user."""
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

        # ensure password control was submitted
        elif not request.form.get("password-control"):
            return apology("must provide password control")

        # ensures password is the same as password control
        elif not request.form.get("password") == request.form.get("password-control"):
            return apology("Password control must be the same as password")

        # hashing the password
        hash = pwd_context.hash(request.form.get("password"))

        # inserts the new user in to the users together with the hash of the password
        insert_username = db.execute("INSERT INTO users (username, hash) VALUES (:username, :hash)", username = request.form.get("username"), hash=hash)

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


@app.route("/sell", methods=["GET", "POST"])
@login_required
def sell():
    """Sell shares of stock."""
    # if user reached route via POST (as by submitting a form via POST)
    if request.method == "POST":

        shares = int(request.form.get("number_shares"))

        # ensure stock symbol is submitted
        if not request.form.get("stock-symbol"):
            return apology("must fill in stock symbol")

        # ensure number of shares is submitted
        elif not request.form.get("number_shares"):
            return apology("must fill in number of shares")

        # ensure number of shares is bigger than zero
        elif shares <= 0:
            return apology("number of shares must be bigger than zero")

        # checks if stock symbol is valid
        stock_quote = lookup(request.form.get("stock-symbol"))
        if not stock_quote:
            return apology("stock isn't valid")

        # select shares from transactions
        select_shares = db.execute("SELECT shares FROM portfolio WHERE userid = :current_user AND stock = :stock",\
        current_user = session["user_id"], stock = stock_quote['symbol'])

        # available shares
        available_shares = int(select_shares[0]["shares"])

        # no shares or not enough
        if not select_shares or available_shares < shares:
            return apology("too little shares")

        profit_shares = float(shares) * stock_quote['price']

        # add profit to current cash user
        add_cash = db.execute("UPDATE users SET cash = cash + :profit_shares WHERE id = :current_user",\
        current_user = session["user_id"], profit_shares = profit_shares)

        # remove sold shares from portfolio
        new_shares = select_shares[0]['shares'] - shares
        update_shares = db.execute("UPDATE portfolio SET shares = :new_shares WHERE userid = :current_user AND stock = :stock",\
        new_shares = new_shares, current_user = session["user_id"], stock = stock_quote['symbol'] )


        return redirect(url_for("index"))

    # else if user reached route via GET (as by clicking a link or via redirect)
    else:
        return render_template("sell.html")

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
        elif not request.form.get("password-control"):
            return apology("must fill in password control")

        # ensures new password is the same as password control
        elif not request.form.get("new_password") == request.form.get("password-control"):
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





