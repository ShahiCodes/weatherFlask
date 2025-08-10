from flask import Flask, request, jsonify
from flask import render_template
from dotenv import load_dotenv
import requests
import os

load_dotenv()

app = Flask(__name__)

@app.route('/')
def home():
    return render_template('index.html')

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