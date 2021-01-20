import os

from cs50 import SQL
from flask import Flask, flash, jsonify, redirect, render_template, request, session
from flask_session import Session
from tempfile import mkdtemp
from werkzeug.exceptions import default_exceptions, HTTPException, InternalServerError
from werkzeug.security import check_password_hash, generate_password_hash

from helpers import apology, login_required, get_random_recipes, search_recipes, get_recipe_info, wiyf_recipes, format_ingredients

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




# Configure session to use filesystem (instead of signed cookies)
app.config["SESSION_FILE_DIR"] = mkdtemp()
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

# Configure CS50 Library to use SQLite database
db = SQL("sqlite:///foodies.db")




@app.route("/", methods=["GET", "POST"])
@login_required
def index():
    if request.method == "GET":
        response = get_random_recipes(15)
        if response == None:
            print("Nothing returned")
            return render_template("index.html")
        else:
            recipes = response["recipes"]
            return render_template("index.html", recipes=recipes)
    else:
        query = request.form.get("searchterm")
        response = search_recipes(query)
        if response == None:
            print("Nothing returned")
            return render_template("index.html")
        else:
            recipes = response["recipes"]
            return render_template("index.html", recipes=recipes)


@app.route("/recipeinfo", methods=["GET", "POST"])
@login_required
def recipe_info():
    if request.method == "POST":
        id = request.form.get("wordid")
        print(id)
        recipe = get_recipe_info(id)
        if recipe == None:
            print("Nothing returned")
            return redirect("/")
        else:
            print(recipe)
            return render_template("recipeinfo.html", recipe=recipe["recipe"])


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


@app.route("/wiyf", methods=["GET", "POST"])
@login_required
def wiyf():
        if request.method == 'POST':
            ingredients_raw = request.form.get("ingredients")
            ingre = format_ingredients(str(ingredients_raw))
            print(ingre)
            response = wiyf_recipes(ingre)
            print(response)
            recipe = response["recipes"]
            return render_template("wiyfrecipes.html", recipe=recipe)
        else:
            return render_template("wiyf.html")



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



def errorhandler(e):
    """Handle error"""
    if not isinstance(e, HTTPException):
        e = InternalServerError()
    return apology(e.name, e.code)


# Listen for errors
for code in default_exceptions:
    app.errorhandler(code)(errorhandler)
