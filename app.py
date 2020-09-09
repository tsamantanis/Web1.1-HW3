import jinja2
import os
import pprint
import pytz
import requests
import sqlite3

from datetime import datetime, timedelta
from dotenv import load_dotenv
from flask import Flask, render_template, request, send_file
from geopy.geocoders import Nominatim
from io import BytesIO
from dateutil.tz import *

app = Flask(__name__)

# Get the API key from the '.env' file
load_dotenv()
API_KEY = os.getenv('API_KEY')

# Initialize Pretty Printer
pp = pprint.PrettyPrinter(indent=4)

my_loader = jinja2.ChoiceLoader([
    app.jinja_loader,
    jinja2.FileSystemLoader('data'),
])
app.jinja_loader = my_loader

@app.route('/')
def home():
    """Displays the homepage with forms for current or historical data."""
    context = {
        'min_date': (datetime.now() - timedelta(days=5)),
        'max_date': datetime.now()
    }
    return render_template('home.html', **context)

def get_letter_for_units(units):
    """Returns a shorthand letter for the given units."""
    return 'F' if units == 'imperial' else 'C' if units == 'metric' else 'K'

@app.route('/results')
def results():
    """Displays results for current weather conditions."""
    city = request.args['city']
    units = request.args['units']

    url = 'http://api.openweathermap.org/data/2.5/weather'
    params = {
        "q": city,
        "appid": API_KEY,
        "units": units
    }

    result_json = requests.get(url, params=params).json()
    date_local = datetime.now()

    context = {
        'date': date_local,
        'city': result_json['name'],
        'description': result_json['weather'][0]['description'],
        'temp': result_json['main']['temp'],
        'humidity': result_json['main']['humidity'],
        'wind_speed': result_json['wind']['speed'],
        'sunrise': datetime.utcfromtimestamp(int(result_json['sys']['sunrise'])).strftime('%Y-%m-%d %H:%M %p'), # I used this answer to format the date https://stackoverflow.com/questions/3682748/converting-unix-timestamp-string-to-readable-date
        'sunset': datetime.utcfromtimestamp(int(result_json['sys']['sunset'])).strftime('%Y-%m-%d %H:%M %p'),
        'units_letter': get_letter_for_units(units),
        # add icon
        'icon_src': 'http://openweathermap.org/img/wn/' + result_json['weather'][0]['icon'] + '.png'
    }

    return render_template('results.html', **context)

def get_min_temp(results):
    """Returns the minimum temp for the given hourly weather objects."""
    min = 100
    for result in results:
        if result['temp'] < min:
            min = result['temp']
    return min

def get_max_temp(results):
    """Returns the maximum temp for the given hourly weather objects."""
    max = 0
    for result in results:
        if result['temp'] > max:
            max = result['temp']
    return max

def get_lat_lon(city_name):
    """Returns latitude and longitude for a given city name. Returns 0, 0 if city is not found"""
    geolocator = Nominatim(user_agent='Weather Application')
    location = geolocator.geocode(city_name)
    if location is not None:
        return location.latitude, location.longitude
    return 0, 0

# Helper function to create Chart.js line chart for historical results
def get_chart_data(lat, lon, units, date):
    """Create and return list of temperatures from the historical data"""
    url = 'http://api.openweathermap.org/data/2.5/onecall/timemachine'
    params = {
        'appid': API_KEY,
        'lat': lat,
        'lon': lon,
        'units': units,
        'dt': date
    }
    result_json = requests.get(url, params=params).json()
    hour_results = result_json['hourly']

    hours = range(24)
    temps = [r['temp'] for r in hour_results]
    return temps


@app.route('/historical_results')
def historical_results():
    """Displays historical weather forecast for a given day."""
    city = request.args['city']
    units = request.args['units']
    date_obj = datetime.now()
    date_in_seconds = date_obj.strftime('%s')

    latitude, longitude = get_lat_lon(city)

    # Stretch challenge error handling. The get_lat_lon method returns 0,0 when the city is not found
    if latitude == 0 and lon == 0:
        return redirect(Exception)
    url = 'http://api.openweathermap.org/data/2.5/onecall/timemachine'

    params = {
        "lat": latitude,
        "lon": longitude,
        "dt": date_in_seconds,
        "appid": API_KEY,
        "units": units
    }

    result_json = requests.get(url, params=params).json()
    result_current = result_json['current']
    result_hourly = result_json['hourly']

    context = {
        'city': city,
        'date': date_obj,
        'lat': latitude,
        'lon': longitude,
        'units': units,
        'units_letter': get_letter_for_units(units), # should be 'C', 'F', or 'K'
        'description': result_current['weather'][0]['description'],
        'temp': result_current['temp'],
        'min_temp': get_min_temp(result_hourly),
        'max_temp': get_max_temp(result_hourly),
        'chart_data': get_chart_data(latitude, longitude, units, date_in_seconds),
        # add icon
        'icon_src': 'http://openweathermap.org/img/wn/' + result_current['weather'][0]['icon'] + '.png'
    }

    return render_template('historical_results.html', **context)

@app.errorhandler(404)
def show_404(error):
    """Display a 404 error page"""
    return render_template('error_page.html', message = "Oops! Looks like you are using an invalid URL.", button = "Home"), 404

@app.errorhandler(400)
def show_400(error):
    """Display an error page when a form submission is missing an input value"""
    return render_template('error_page.html', message = "There was an error in your form submission.\n \nCheck that all fields are completed and try again.", button = "Try Again"), 400

@app.errorhandler(Exception)
def show_500(error):
    """Display an error page when a city name is invalid or not found"""
    return render_template('error_page.html', message = "We couldn't find the city you entered. \n \nPlease check the grammar and try again.", button = "Try Again")

if __name__ == '__main__':
    app.run(debug=True)
