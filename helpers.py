import os
import requests
import urllib.parse

from flask import redirect, render_template, request, session
from functools import wraps




def login_required(f):
    """
    Decorate routes to require login.

    http://flask.pocoo.org/docs/1.0/patterns/viewdecorators/
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if session.get("user_id") is None:
            return redirect("/login")
        return f(*args, **kwargs)
    return decorated_function


def get_random_recipes(number):


    # Contact API
    try:
        api_key = "6e34aecc6e544e778bc4e457a39498a3"
        response = requests.get(f"https://api.spoonacular.com/recipes/random?number={number}&tags=seafood&apiKey={api_key}")
        response.raise_for_status()
    except requests.RequestException:
        return None

    # Parse response
    try:
        recipe = response.json()
        return {
            "recipes": recipe["recipes"]
        }
    except (KeyError, TypeError, ValueError):
        return None


def search_recipes(query):


    # Contact API
    try:
        api_key = "6e34aecc6e544e778bc4e457a39498a3"
        response = requests.get(f"https://api.spoonacular.com/recipes/complexSearch?query={query}&apiKey={api_key}")
        response.raise_for_status()
    except requests.RequestException:
        return None

    # Parse response
    try:
        recipe = response.json()
        return {
            "recipes": recipe["results"]
        }
    except (KeyError, TypeError, ValueError):
        return None


def wiyf_recipes(ingredients):


    # Contact API
    try:
        api_key = "6e34aecc6e544e778bc4e457a39498a3"
        response = requests.get(f"https://api.spoonacular.com/recipes/findByIngredients?ingredients={ingredients}&number=6&apiKey={api_key}")
        response.raise_for_status()
    except requests.RequestException:
        return None

    # Parse response
    try:
        recipe = response.json()
        return {
            "recipes": recipe[0]
        }
    except (KeyError, TypeError, ValueError):
        return None


def get_recipe_info(id):


    # Contact API
    try:
        api_key = "6e34aecc6e544e778bc4e457a39498a3"
        response = requests.get(f"https://api.spoonacular.com/recipes/{id}/information?includeNutrition=false&apiKey={api_key}")
        response.raise_for_status()
    except requests.RequestException:
        return None

    # Parse response
    try:
        recipe = response.json()
        return {
            "recipe": recipe
        }
    except (KeyError, TypeError, ValueError):
        return None


def format_ingredients(ingredients):
    ingre = ""
    for i in range(len(ingredients)):
        if ingredients[i] == ",":
            ingre += ","
            ingre += "+"
        else:
            ingre += ingredients[i]
    return ingre



def apology(message, code=400):
    """Render message as an apology to user."""
    def escape(s):
        """
        Escape special characters.

        https://github.com/jacebrowning/memegen#special-characters
        """
        for old, new in [("-", "--"), (" ", "-"), ("_", "__"), ("?", "~q"),
                         ("%", "~p"), ("#", "~h"), ("/", "~s"), ("\"", "''")]:
            s = s.replace(old, new)
        return s
    return render_template("apology.html", top=code, bottom=escape(message)), code