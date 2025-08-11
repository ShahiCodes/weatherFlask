from flask import Flask, request, jsonify, flash, url_for, redirect
from flask import render_template
from dotenv import load_dotenv
import requests
import json
import os

load_dotenv()

app = Flask(__name__)
app.secret_key = "super_secret_key_123" 

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


@app.route('/weather', methods=['GET'])
def get_weather():
    city = request.args.get('city') #because we are using GET method
    api_key = os.getenv("API_KEY")
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