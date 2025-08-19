from flask import Blueprint, request, jsonify, render_template, flash, redirect, url_for
import asyncio, aiohttp, requests
from sqlalchemy import func
from sqlalchemy.exc import IntegrityError
from app import db
from app.models import FavouriteCities

bp = Blueprint("routes", __name__)

FAV_FILE = "favourite.json"

@bp.route("/")
def home():
    return render_template("index.html")

@bp.route("/setFav", methods=["POST"])
def set_favourite():
    raw_city = (request.form.get("city") or "").strip()
    if not raw_city:
        flash("Please enter a city name.")
        return redirect(url_for("routes.home"))

    city_name = raw_city.title()
    # 
    existing = FavouriteCities.query.filter(
        func.lower(FavouriteCities.name) == city_name.lower()
    ).first()
    
    if existing:
        flash(f"{city_name} is already in your favourities")
        return redirect(url_for("routes.home"))
    
    db.session.add(FavouriteCities(name=city_name)) 
    
    try:
        db.session.commit()
        flash(f"{city_name} is added to your favourites")
    except IntegrityError:
        db.session.rollback()
        flash(f"{city_name} already exists") 
    
    return redirect(url_for("routes.home"))
    

@bp.route("/showFav", methods=["GET"])
def show_fav():
    fav_cities = FavouriteCities.query.order_by(FavouriteCities.name).all()
    return render_template("favCities.html", cities=[c.name for c in fav_cities])

@bp.route("/deleteFav", methods=["POST"])
def delete_fav():
    cityName = request.form.get("city")
    
    fav_city = FavouriteCities.query.filter(
        FavouriteCities.name.ilike(cityName)
    ).first()
    
    if fav_city:
        db.session.delete(fav_city)
        db.session.commit()
        flash(f"{cityName} has been removed from your favourites")
        #Important Note
        # fav_city is not just raw data — it’s a "Python object" mapped 
        # to the row in favourite_cities table. This is why we dont need to 
        # mention the table name while writing delete
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

    favourites = [fav.name for fav in FavouriteCities.query.all()]
    

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
