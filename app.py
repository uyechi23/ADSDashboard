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
    con = sqlite3.connect(f'{name}.sqlite3')
    cur = con.cursor()
    
    # query oldest timestamp
    query = f'\
        SELECT timestamp FROM raindata\
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
    
    # calculate total raintime
    query = f'\
        SELECT (runningraintime) FROM raindata\
        ORDER BY timestamp DESC\
    '
    records = con.execute(query).fetchone()
    raintime = records[0]
    days, remainder = divmod(raintime, 86400)
    hours, remainder = divmod(remainder, 3600)
    minutes, seconds = divmod(remainder, 60)
    raintime_string = f'{int(days)}d {int(hours):02}h {int(minutes):02}m {seconds:.3}s'    
    
    # rain time and total running time 
    timers = {
        'runtime':runtime_string,
        'raintime':raintime_string
    }
    
    # query device info
    query = f'\
        SELECT * FROM miscdata\
        ORDER BY timestamp DESC\
    '
    record_misc = cur.execute(query).fetchone()
    
    query = f'\
        SELECT * FROM raindata\
        ORDER BY timestamp DESC\
    '
    record_rain = cur.execute(query).fetchone()
    
    # device information dict
    deviceinfo = {
        'name':f'{name}',
        'recordnum_misc':f'{record_misc[0]}',
        'recordnum_rain':f'{record_rain[0]}',
        'mac':f'{record_misc[1]}',
        'status':f'{record_misc[2]}',
        'temp':f'{record_misc[3]}',
        'hum':f'{record_misc[4]}',
        'raining':f'{record_rain[1]}'
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
    inputmiscdata - Input data to database with Flask URL Parameters (miscellaneous data)
    @param name - the name of the device; will be set on the first time it polls data to this route
    @param macaddress - the MAC address of the device
    @param status - a short status message about the device's operation
    @param temp - the current temperature, measured in Celsius
    @param hum - the current humidity, measured in %
    
    @return JSON object containing the database row data
"""
@app.route("/inputdata/misc/<string:name>/<string:macaddress>/<string:status>/<float:temp>/<float:hum>")
def inputmiscdata(name, macaddress, status, temp, hum):
    # get the current time
    currtime = datetime.now().astimezone(pytz.timezone('Canada/Pacific')).strftime('%Y-%m-%d %H:%M:%S.%f')
    
    # create a database connection and cursor
    con = sqlite3.connect(f'{name}.sqlite3')
    cur = con.cursor()
    
    # query to create a table if it doesn't already exist
    # to store the above data
    query = f'\
        CREATE TABLE IF NOT EXISTS miscdata (\
            id INTEGER PRIMARY KEY NOT NULL,\
            macaddress TEXT NOT NULL,\
            status TEXT NOT NULL,\
            temperature FLOAT NOT NULL,\
            humidity FLOAT NOT NULL,\
            timestamp TIMESTAMP NOT NULL\
        )\
    '
    cur.execute(query)
    
    # insert data
    query = f'\
        INSERT INTO miscdata (macaddress, status, temperature, humidity, timestamp)\
        VALUES (?, ?, ?, ?, ?)\
    '
    cur.execute(query, (macaddress, status, temp, hum, currtime))
    con.commit()
    
    # close database connection
    con.close()
    
    return jsonify(
        name=name,
        macaddress=macaddress,
        status=status,
        temperature=temp,
        humidity=hum,
        timestamp=currtime
    )
    
    
"""
    inputraindata - Input data to database whenever the rain changes
    @param name - the name of the device
    @param raining - 0 if not raining, 1 if raining
"""
@app.route("/inputdata/rain/<string:name>/<int:raining>")
def inputraindata(name, raining):
    # get the current time
    currtime = datetime.now().astimezone(pytz.timezone('Canada/Pacific')).strftime('%Y-%m-%d %H:%M:%S.%f')
    
    # create a database connection and cursor
    con = sqlite3.connect(f'{name}.sqlite3')
    cur = con.cursor()
    
    # query to create a table if it doesn't already exist
    query = f'\
        CREATE TABLE IF NOT EXISTS raindata (\
            id INTEGER PRIMARY KEY NOT NULL,\
            raining INTEGER NOT NULL,\
            runningraintime FLOAT NOT NULL,\
            timestamp TIMESTAMP NOT NULL\
        ) \
    '
    cur.execute(query)
    con.commit()
    
    # check and add data if missing first row
    query = f'SELECT * FROM raindata'
    if len(cur.execute(query).fetchall()) == 0:
        query = f'\
                INSERT INTO raindata (raining, runningraintime, timestamp)\
                VALUES (?, ?, ?)\
            '
        cur.execute(query, (raining, 0, currtime))
        con.commit()
    
    # check if it was last raining
    query = f'\
        SELECT * FROM raindata\
        ORDER BY timestamp DESC\
    '
    recentrecord = cur.execute(query).fetchone()
    recentrainstatus = recentrecord[1]
    
    # if the last status said it was raining, we should add the
    # time difference between the last record and the current record
    # to the running total of raintime
    # if it wasn't raining, we just carry the running total forward
    if recentrainstatus == 1:
        query = f'\
            SELECT * FROM raindata\
            ORDER BY timestamp DESC\
        '
        record = cur.execute(query).fetchone()
        lastrecordtime = datetime.strptime(record[3], "%Y-%m-%d %H:%M:%S.%f")
        timetoadd = datetime.strptime(currtime, "%Y-%m-%d %H:%M:%S.%f") - lastrecordtime
        secondstoadd = timetoadd.total_seconds()
        newraintime = record[2] + secondstoadd
    else:
        query = f'\
            SELECT runningraintime FROM raindata\
            ORDER BY timestamp DESC\
        '
        newraintime = cur.execute(query).fetchone()[0]
    
    # insert data
    query = f'\
        INSERT INTO raindata (raining, runningraintime, timestamp)\
        VALUES (?, ?, ?)\
    '
    cur.execute(query, (raining, newraintime, currtime))
    con.commit()
    
    # close the database connection
    con.close()
    
    return jsonify(
        name=name,
        raining=raining,
        rainingruntime=newraintime,
        timestamp=currtime
    )
    