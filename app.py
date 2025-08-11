from flask import Flask, request, jsonify, flash, url_for, redirect
from flask import render_template
from dotenv import load_dotenv
import asyncio
import aiohttp
import requests
import json
import os

load_dotenv()

app = Flask(__name__)
app.secret_key = "super_secret_key_123" 
API_KEY = os.getenv("API_KEY")
API_URL = "http://api.openweathermap.org/data/2.5/weather"

FAV_FILE = 'favourite.json'

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/setFav', methods = ['POST'])
def set_favourite():
    cityName = request.form.get('city')
    
    with open(FAV_FILE, 'r') as f:
        favourites = json.load(f)
        
    if any(fav.lower() == cityName.lower() for fav in favourites):
        flash(f"{cityName} is already in your favourite")
        return redirect(url_for("home"))
    favourites.append(cityName)
    with open(FAV_FILE, 'w') as f:
        json.dump(favourites, f, indent=2)
    
    flash(f"{cityName} is added to your favourite")
    return redirect(url_for("home"))

@app.route('/showFav', methods=['GET'])
def show_fav():
    try:
        with open('favourite.json', 'r') as f:
            fav_cities = json.load(f)
    except FileNotFoundError:
        fav_cities = []

    return render_template('favCities.html', cities = fav_cities)

@app.route('/deleteFav', methods=['POST'])
def delete_fav():
    cityName = request.form.get('city')
    
    try:
        with open(FAV_FILE, 'r') as f:
            favourites = json.load(f)
    except FileNotFoundError:
        favourites = []

    if cityName in favourites:
        favourites.remove(cityName)
        with open(FAV_FILE, 'w') as f:
            json.dump(favourites, f, indent=2)
        flash(f"{cityName} has been removed from your favourites")
    else:
        flash(f"{cityName} is not in your favourites")
    
    return redirect(url_for("show_fav"))


@app.route('/weather', methods=['GET'])
def get_weather():
    city = request.args.get('city') #because we are using GET method
    api_key = API_KEY
    url = f"http://api.openweathermap.org/data/2.5/weather?q={city}&units=metric&appid={api_key}"
    response = requests.get(url)
    if response.status_code == 200:
        data = response.json()
        weather_data = ({
            "city": data['name'],
            "weather": data['weather'][0]['description'],
            "temperature": data['main']['temp'],
            "feelsLike": data['main']['feels_like'],
            "humidity": data['main']['humidity'],
            "windSpeed": data['wind']['speed'],
            "coordinate": data['coord'],
        })   
    else:
        return jsonify({"error": "some error occured"}), response.status_code
    
    return render_template('weather.html', weather_data=weather_data)

async def fetch_weather(session, city):
    params = {"q": city, "appid": API_KEY, "units": "metric"}
    try:
        async with session.get(API_URL, params = params) as response:
            if response.status == 200:
                return {city: await response.json()}
            else:
                return {city: f"Error {response.status}"}
    except Exception as e:
        return {city: f"Request failed: {str(e)}"}

async def get_all_weather(cities):
    async with aiohttp.ClientSession() as session:
        tasks = [fetch_weather(session, city) for city in cities]
        results = await asyncio.gather(*tasks, return_exceptions=False)
    return results

@app.route('/weatherAll', methods=['GET'])
def weather_all():
    try:
        with open(FAV_FILE, 'r') as f:
            favourites = json.load(f)
    except FileNotFoundError:
        favourites = []

    results = asyncio.run(get_all_weather(favourites))
    # return jsonify(results)
    weather_data_list = []
    for city_result in results:
        for city, data in city_result.items():
            if isinstance(data, dict):  # successful fetch
                weather_data_list.append({
                    "city": data['name'],
                    "weather": data['weather'][0]['description'],
                    "temperature": data['main']['temp'],
                    "feelsLike": data['main']['feels_like'],
                    "humidity": data['main']['humidity'],
                    "windSpeed": data['wind']['speed'],
                    "coordinate": data['coord'],
                })
            else:  # error message
                weather_data_list.append({
                    "city": city,
                    "weather": data,
                    "temperature": None,
                    "feelsLike": None,
                    "humidity": None,
                    "windSpeed": None,
                    "coordinate": None,
                })

    return render_template('weatherAll.html', weather_data=weather_data_list)