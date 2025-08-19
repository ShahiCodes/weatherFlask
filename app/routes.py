from flask import Blueprint, request, jsonify, render_template, flash, redirect, url_for
import asyncio, aiohttp, requests, json, os
from app import db
from app.models import FavouriteCities

bp = Blueprint("routes", __name__)

FAV_FILE = "favourite.json"

@bp.route("/")
def home():
    return render_template("index.html")

@bp.route("/setFav", methods=["POST"])
def set_favourite():
    cityName = request.form.get("city")
    
    try:
        with open(FAV_FILE, "r") as f:
            favourites = json.load(f)
    except FileNotFoundError:
        favourites = []

    if any(fav.lower() == cityName.lower() for fav in favourites):
        flash(f"{cityName} is already in your favourite")
        return redirect(url_for("routes.home"))

    favourites.append(cityName)
    with open(FAV_FILE, "w") as f:
        json.dump(favourites, f, indent=2)
    
    flash(f"{cityName} is added to your favourites")
    return redirect(url_for("routes.home"))

@bp.route("/showFav", methods=["GET"])
def show_fav():
    try:
        with open(FAV_FILE, "r") as f:
            fav_cities = json.load(f)
    except FileNotFoundError:
        fav_cities = []
    return render_template("favCities.html", cities=fav_cities)

@bp.route("/deleteFav", methods=["POST"])
def delete_fav():
    cityName = request.form.get("city")
    try:
        with open(FAV_FILE, "r") as f:
            favourites = json.load(f)
    except FileNotFoundError:
        favourites = []

    if cityName in favourites:
        favourites.remove(cityName)
        with open(FAV_FILE, "w") as f:
            json.dump(favourites, f, indent=2)
        flash(f"{cityName} has been removed from your favourites")
    else:
        flash(f"{cityName} is not in your favourites")
    
    return redirect(url_for("routes.show_fav"))

@bp.route("/weather", methods=["GET"])
def get_weather():
    from config import Config
    API_KEY = Config.API_KEY
    API_URL = Config.API_URL

    city = request.args.get("city")
    url = f"{API_URL}?q={city}&units=metric&appid={API_KEY}"
    response = requests.get(url)

    if response.status_code == 200:
        data = response.json()
        weather_data = {
            "city": data["name"],
            "weather": data["weather"][0]["description"],
            "temperature": data["main"]["temp"],
            "feelsLike": data["main"]["feels_like"],
            "humidity": data["main"]["humidity"],
            "windSpeed": data["wind"]["speed"],
            "coordinate": data["coord"],
        }
    else:
        return jsonify({"error": "some error occurred"}), response.status_code
    
    return render_template("weather.html", weather_data=weather_data)

# Async fetching
async def fetch_weather(session, city, API_URL, API_KEY):
    params = {"q": city, "appid": API_KEY, "units": "metric"}
    try:
        async with session.get(API_URL, params=params) as response:
            if response.status == 200:
                return {city: await response.json()}
            else:
                return {city: f"Error {response.status}"}
    except Exception as e:
        return {city: f"Request failed: {str(e)}"}

async def get_all_weather(cities, API_URL, API_KEY):
    async with aiohttp.ClientSession() as session:
        tasks = [fetch_weather(session, city, API_URL, API_KEY) for city in cities]
        results = await asyncio.gather(*tasks, return_exceptions=False)
    return results

@bp.route("/weatherAll", methods=["GET"])
def weather_all():
    from config import Config
    API_KEY = Config.API_KEY
    API_URL = Config.API_URL

    try:
        with open(FAV_FILE, "r") as f:
            favourites = json.load(f)
    except FileNotFoundError:
        favourites = []

    results = asyncio.run(get_all_weather(favourites, API_URL, API_KEY))

    weather_data_list = []
    for city_result in results:
        for city, data in city_result.items():
            if isinstance(data, dict):
                weather_data_list.append({
                    "city": data["name"],
                    "weather": data["weather"][0]["description"],
                    "temperature": data["main"]["temp"],
                    "feelsLike": data["main"]["feels_like"],
                    "humidity": data["main"]["humidity"],
                    "windSpeed": data["wind"]["speed"],
                    "coordinate": data["coord"],
                })
            else:
                weather_data_list.append({
                    "city": city,
                    "weather": data,
                    "temperature": None,
                    "feelsLike": None,
                    "humidity": None,
                    "windSpeed": None,
                    "coordinate": None,
                })

    return render_template("weatherAll.html", weather_data=weather_data_list)
