from flask import Flask, render_template, jsonify, send_from_directory
import sqlite3
from datetime import datetime
import pytz
from openmeteo_py import Options,OWmanager
import os   

app = Flask(__name__)

@app.route("/")
def default():
    return f'ADS Dashboard is running. Current time: {datetime.now()}'
@app.route('/favicon.ico') 
def favicon(): 
    return send_from_directory(os.path.join(app.root_path, 'static'), 'favicon.ico', mimetype='image/vnd.microsoft.icon')

"""
    home - the ADS Dashboard's main page
    @param name - the name of the device you'd like to view
    
    @return HTTP response containing Jinja2-formatted HTML code
"""
@app.route("/dashboard/<string:name>")
def dashboard(name):
    # create a database connection and cursor
    con = sqlite3.connect('database.sqlite3')
    cur = con.cursor()
    
    # query oldest timestamp
    query = f'\
        SELECT timestamp FROM {name}\
        ORDER BY timestamp ASC\
    '
    records = con.execute(query).fetchall()
    oldest = datetime.strptime(records[0][0], "%Y-%m-%d %H:%M:%S.%f")
    newest = datetime.strptime(records[len(records)-1][0], "%Y-%m-%d %H:%M:%S.%f")
    
    # calculate the time difference and parse into string
    runtime = newest-oldest
    totalseconds = runtime.total_seconds()
    days, remainder = divmod(totalseconds, 86400)
    hours, remainder = divmod(remainder, 3600)
    minutes, seconds = divmod(remainder, 60)
    runtime_string = f'{int(days)}d {int(hours):02}h {int(minutes):02}m {seconds:.3}s'
    
    # rain time and total running time 
    timers = {
        'runtime':runtime_string
    }
    
    # query device info
    query = f'\
        SELECT * FROM {name}\
        ORDER BY timestamp DESC\
    '
    record = cur.execute(query).fetchone()
    
    deviceinfo = {
        'recordnum':f'{record[0]}',
        'name':f'{name}',
        'mac':f'{record[1]}',
        'status':f'{record[2]}',
        'raining':f'{record[3]}',
        'temp':f'{record[4]}',
        'hum':f'{record[5]}',
    }
    
    con.close()
    
    # Forecast API Call (OpenMeteo)
    # currently set to PORTLAND, OR coordinates
    latitude = 45.5732
    longitude = -122.7276

    # configuration settings for Weather API
    options = Options(latitude,longitude,timezone="Canada/Pacific",current_weather=True)
    mgr = OWmanager(options)
    meteo = mgr.get_data()
    
    # assemble tuples for Jinja2 Templating
    forecast_data = {
        'time':datetime.strptime(
            meteo['current_weather']['time'], "%Y-%m-%dT%H:%M").strftime("%B %d, %Y at %I:%m %p"),
        'lat':meteo['latitude'],
        'lon':meteo['longitude'],
        'elevation':meteo['elevation'],
        'timezone':meteo['timezone_abbreviation'],
        'temp_c':meteo['current_weather']['temperature'],
        'temp_f':(meteo['current_weather']['temperature'] * 9 / 5) + 32,
        'windspeed':meteo['current_weather']['windspeed'],
        'winddirection':meteo['current_weather']['winddirection'],
    }
    
    return render_template("index.html", forecast_data=forecast_data, timers=timers, deviceinfo=deviceinfo)

"""
    inputdata - Input data to database with Flask URL Parameters
    @param name - the name of the device; will be set on the first time it polls data to this route
    @param macaddress - the MAC address of the device
    @param status - a short status message about the device's operation
    @param raining - integer either 0 or 1 (0 indicates no rain)
    @param temp - the current temperature, measured in Celsius
    @param hum - the current humidity, measured in %
    
    @return JSON object containing the database row data
"""
@app.route("/inputdata/<string:name>/<string:macaddress>/<string:status>/<int:raining>/<float:temp>/<float:hum>")
def inputdata(name, macaddress, status, raining, temp, hum):
    # get the current time
    currtime = datetime.now().astimezone(pytz.timezone('Canada/Pacific')).strftime('%Y-%m-%d %H:%M:%S.%f')
    
    # create a database connection and cursor
    con = sqlite3.connect('database.sqlite3')
    cur = con.cursor()
    
    # query to create a table if it doesn't already exist
    # to store the above data
    query = f'\
        CREATE TABLE IF NOT EXISTS {name} (\
            id INTEGER PRIMARY KEY NOT NULL,\
            macaddress TEXT NOT NULL,\
            status TEXT NOT NULL,\
            raining INTEGER NOT NULL,\
            temperature FLOAT NOT NULL,\
            humidity FLOAT NOT NULL,\
            timestamp TIMESTAMP NOT NULL\
        )\
    '
    cur.execute(query)
    
    # insert data
    query = f'\
        INSERT INTO {name} (macaddress, status, raining, temperature, humidity, timestamp)\
        VALUES (?, ?, ?, ?, ?, ?)\
    '
    cur.execute(query, (macaddress, status, raining, temp, hum, currtime))
    con.commit()
    
    # close database connection
    con.close()
    
    return jsonify(
        name=name,
        macaddress=macaddress,
        status=status,
        raining=raining,
        temperature=temp,
        humidity=hum,
        timestamp=currtime
    )