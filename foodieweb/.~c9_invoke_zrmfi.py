import os

from cs50 import SQL
from flask import Flask, flash, jsonify, redirect, render_template, request, session
from flask_session import Session
from tempfile import mkdtemp
from werkzeug.exceptions import default_exceptions, HTTPException, InternalServerError
from werkzeug.security import check_password_hash, generate_password_hash

from helpers import apology, login_required, lookup, usd

# Configure application
app = Flask(__name__)

# Ensure templates are auto-reloaded
app.config["TEMPLATES_AUTO_RELOAD"] = True

# Ensure responses aren't cached
@app.after_request
def after_request(response):
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    response.headers["Expires"] = 0
    response.headers["Pragma"] = "no-cache"
    return response

# Custom filter
app.jinja_env.filters["usd"] = usd

# Configure session to use filesystem (instead of signed cookies)
app.config["SESSION_FILE_DIR"] = mkdtemp()
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

# Configure CS50 Library to use SQLite database
db = SQL("sqlite:///finance.db")

# Make sure API key is set
if not os.environ.get("API_KEY"):
    raise RuntimeError("API_KEY not set")


@app.route("/")
@login_required
def index():
    response = get_random_recipes(12)
    print(response["recipes"])
    return render_template("index.html")


@app.route("/buy", methods=["GET", "POST"])
@login_required
def buy():
    if request.method == 'POST':
        symbol = request.form.get("symbol")
        shares = request.form.get("shares")
        response = lookup(symbol)
        current_id = session["user_id"]
        cash = db.execute("SELECT cash FROM users WHERE id = ?", current_id)

        if symbol == '':
            return apology("Enter a stock symbol")
        elif response is None:
            return apology("This stock does not exist")
        elif shares == '':
            return apology("Select the amount of shares you want to buy")
        else:
            stockprice = response["price"]
            amount = stockprice * int(shares)
            if cash[0]["cash"] < amount:
                return apology("Insufficient funds")
            else:
                stocks = db.execute("SELECT * FROM stocks WHERE user_id = ?", current_id)
                for row in stocks:
                    if symbol == row["symbol"]:
                        new_share = int(row["shares"]) + int(shares)
                        db.execute("UPDATE stocks SET shares = ? WHERE user_id = ? AND symbol = ?", new_share, current_id, symbol)
                        db.execute("INSERT INTO history (user_id, symbol, shares, price) VALUES (?, ?, ?, ?)", current_id, symbol, int(shares), amount)
                        new_cash = float(cash[0]["cash"]) - amount
                        db.execute("UPDATE users SET cash = ? WHERE id = ?", new_cash, current_id)
                        return redirect("/")
                    else:
                        continue
                db.execute("INSERT INTO stocks (user_id, symbol, shares) VALUES (?, ?, ?)", current_id, symbol, int(shares))
                db.execute("INSERT INTO history (user_id, symbol, shares, price) VALUES (?, ?, ?, ?)", current_id, symbol, int(shares), amount)
                new_cash = float(cash[0]["cash"]) - amount
                db.execute("UPDATE users SET cash = ? WHERE id = ?", new_cash, current_id)
                return redirect("/")
    else:
        return render_template("buy.html")


@app.route("/history")
@login_required
def history():
    history = db.execute("SELECT * FROM history WHERE user_id = ?", session["user_id"])
    for row in history:
        row["price"] = usd(float(row["price"]))
    return render_template("history.html", history=history)


@app.route("/login", methods=["GET", "POST"])
def login():
    """Log user in"""

    # Forget any user_id
    session.clear()

    # User reached route via POST (as by submitting a form via POST)
    if request.method == "POST":

        # Ensure username was submitted
        if not request.form.get("username"):
            return apology("must provide username", 403)

        # Ensure password was submitted
        elif not request.form.get("password"):
            return apology("must provide password", 403)

        # Query database for username
        rows = db.execute("SELECT * FROM users WHERE username = :username",
                          username=request.form.get("username"))

        # Ensure username exists and password is correct
        if len(rows) != 1 or not check_password_hash(rows[0]["hash"], request.form.get("password")):
            return apology("invalid username and/or password", 403)

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


@app.route("/quote", methods=["GET", "POST"])
@login_required
def quote():
    if request.method == 'POST':
        symbol = request.form.get("stocksymbol")
        response = lookup(symbol)
        if response is None:
            return apology("This stock does not exist")
        else:
            name = response['name']
            symbol = response['symbol']
            price = response['price']
            return render_template("quoted.html", name=name, symbol=symbol, price=price)
    else:
        return render_template("quote.html")


@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == 'POST':
        name = request.form.get("username")
        password = request.form.get("password")
        password_again = request.form.get("passwordagain")
        user_exist = db.execute("SELECT username FROM users WHERE username=?", name)
        if name is '':
            return apology("You have to enter a username")
        elif len(user_exist) > 0:
            return apology("Username has already been used")
        elif password is '' or password_again is '':
            return apology("You have to enter your password twice")
        elif not password == password_again:
            return apology("Make sure you type the same password twice")
        else:
            hash_password = generate_password_hash(password)
            db.execute("INSERT INTO users (username, hash) VALUES (?, ?)", name, hash_password)
            return redirect("/")
    else:
        return render_template("register.html")




@app.route("/sell", methods=["GET", "POST"])
@login_required
def sell():
    current_id = session["user_id"]
    stocks = db.execute("SELECT symbol, shares FROM stocks WHERE user_id = ?", current_id)
    user_cash = db.execute("SELECT cash FROM users WHERE id = ?", current_id)
    if request.method == 'POST':
        symbol = request.form.get("symbol")
        shares = request.form.get("shares")
        if symbol is '':
            return apology("You must select a stock")
        elif shares is '':
            return apology("You must enter the number of share you wish to sell")
        else:
            for row in stocks:
                if row["symbol"] == symbol:
                    companyshare = row["shares"]
                    if int(shares) <= companyshare:
                        response = lookup(symbol)
                        #add cash to users cash
                        sellamount = float(response["price"]) * int(shares)
                        cash = float(user_cash[0]["cash"])
                        totalcash = sellamount + cash
                        db.execute("UPDATE users SET cash = ? WHERE id = ?", totalcash, current_id)
                        #update stocks owned
                        new_share = companyshare - int(shares)
                        if new_share == 0:
                            db.execute("DELETE FROM stocks WHERE user_id = ? AND symbol = ?", current_id, symbol)
                        else:
                            db.execute("UPDATE stocks SET shares = ? WHERE user_id = ? AND symbol = ?", new_share, current_id, symbol)
                        #add transaction to history
                        soldshare = -1 * int(shares)
                        db.execute("INSERT INTO history (user_id, symbol, shares, price) VALUES (?, ?, ?, ?)", current_id, symbol, soldshare, sellamount)
                        return redirect("/")
                    else:
                        return apology("You don't own this much shares")
            return apology("You don't own this stock")
    else:
        return render_template("sell.html", stocks=stocks)

@app.route("/deposit", methods=['GET', 'POST'])
@login_required
def deposit():
    if request.method == 'POST':
        str_deposit = request.form.get("deposit")
        if str_deposit == '':
            return apology("Enter an amount to deposit")
        deposit = float(request.form.get("deposit"))
        user = db.execute("SELECT cash FROM users WHERE id = ?", session["user_id"])
        new_cash = deposit + float(user[0]["cash"])
        db.execute("UPDATE users SET cash = ? WHERE id = ?", new_cash, session["user_id"])
        return redirect("/")
    else:
        return render_template("deposit.html")


def errorhandler(e):
    """Handle error"""
    if not isinstance(e, HTTPException):
        e = InternalServerError()
    return apology(e.name, e.code)


# Listen for errors
for code in default_exceptions:
    app.errorhandler(code)(errorhandler)
