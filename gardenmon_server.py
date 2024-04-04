import datetime
from enum import Enum
from flask import Flask, jsonify, request
from flask_cors import CORS, cross_origin
import local_options
import mysql.connector

app = Flask(__name__, static_folder='GardenMonWebsite')
cors = CORS(app)
app.config['CORS_HEADERS'] = 'Content-Type'

VALID_COLUMNS = {"ambient_humidity", "ambient_light_lx", "ambient_temp_f", "cpu_temp_f", "soil_moisture_level", "soil_moisture_val", "soil_temp_f"}

class Device(Enum):
    gardenmon = "device = 'gardenmon'"
    gardenmon_two = "device = 'gardenmon2'"

class TimeGrouping(Enum):
    all_data = ""
    fifteen_min = "DATE_ADD(DATE_FORMAT(insert_time, '%Y-%m-%d %H'), INTERVAL FLOOR(MINUTE(insert_time) / 15) * 15 MINUTE)"
    hour = "DATE_FORMAT(insert_time, '%Y-%m-%d %H')"
    day = "DATE_FORMAT(insert_time, '%Y-%m-%d')"
    month = "DATE_FORMAT(insert_time, '%Y-%m')"

def create_db_connection():
    try:
        connection = mysql.connector.connect(
            database=local_options.database_name,
            user=local_options.database_user,
            password=local_options.database_password
        )
        if connection.is_connected():
            return connection
    except Exception as e:
        raise e

@app.route('/')
def index():
    return app.send_static_file('index.html')


@app.route('/data', methods=['GET'])
@cross_origin()
def query_data():
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')
    grouping_period = request.args.get('grouping_period')
    device = request.args.get("device")
    columns = request.args.getlist("columns")
    
    if len(columns) > 0:
        if not all(el in VALID_COLUMNS for el in columns):
            return jsonify({"error": f"column must be in {VALID_COLUMNS}"})
    else:
        columns = list(VALID_COLUMNS)

    try:
        device = Device[device].value
    except:
        if device is not None:
            return jsonify({"error": "device must either be unspecified, gardenmon, or gardenmon_two"})
        device = "TRUE"

    if not start_date or not end_date or not grouping_period:
        return jsonify({"error": "must specify start_date, end_date, and grouping_period"}), 400

    try:
        start_date = datetime.datetime.strptime(start_date, '%Y-%m-%d-%H-%M')
        end_date = datetime.datetime.strptime(end_date, '%Y-%m-%d-%H-%M')
        if start_date >= end_date:
            return jsonify({"error": "start_date must be before end_date"}), 400
    except Exception as e:
        return jsonify({"error": "Use date format YYYY-MM-DD-HH-MM"}), 400

    try:
        time_grouping = TimeGrouping[grouping_period]
    except Exception as e:
        return jsonify({"error": "grouping_period must be all_data, fifteen_min, hour, day, or month"})

    connection = create_db_connection()
    cursor = connection.cursor(dictionary=True)
    if time_grouping is TimeGrouping.all_data:
        string_columns = ','.join(columns)
        query = f"""
            SELECT
                {string_columns},
                UNIX_TIMESTAMP(insert_time) as insert_time,
                device
            FROM {local_options.database_table}
            WHERE insert_time >= '{start_date}' AND insert_time < '{end_date}' and {device}
        """
    else:
        avg_columns = ','.join([f"AVG({el}) as {el}" for el in columns])
        query = f"""
            SELECT
                {avg_columns},
                UNIX_TIMESTAMP({time_grouping.value}) AS insert_time,
                device
            FROM {local_options.database_table}
            WHERE insert_time >= '{start_date}' AND insert_time < '{end_date}' and {device}
            GROUP BY {time_grouping.value}, device
        """
    cursor.execute(query)
    rows = cursor.fetchall()
    cursor.close()
    connection.close()
    return jsonify(rows), 200

if __name__ == '__main__':
    app.run(host="0.0.0.0", debug=False)
