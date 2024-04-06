from datetime import datetime
from enum import Enum
from flask import Flask, jsonify, request
from flask_cors import CORS, cross_origin
import local_options
import logging
import mysql.connector
from typing import List

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
        else:
            raise RuntimeError
    except Exception:
        raise RuntimeError("database connection failed")

def get_data(columns, device, start_date, end_date, grouping_period):
    if len(columns) > 0:
        if not all(el in VALID_COLUMNS for el in columns):
            raise ValueError(f"columns must be in {VALID_COLUMNS}")
    else:
        columns = list(VALID_COLUMNS)
    
    if device:
        try:
            device = Device[device].value
        except KeyError:
            raise ValueError(f"device must either be unspecified or in {[device.name for device in Device]}")
    else:
        device = "TRUE"
    
    if not start_date or not end_date or not grouping_period:
        raise ValueError("must specify start_date, end_date, and grouping_period")
    try:
        start_date = datetime.strptime(start_date, '%Y-%m-%d-%H-%M')
        end_date = datetime.strptime(end_date, '%Y-%m-%d-%H-%M')
    except ValueError:
        raise ValueError("use date format: YYYY-MM-DD-HH-MM")
    if start_date >= end_date:
        raise ValueError("start_date must be before end_date")

    try:
        time_grouping = TimeGrouping[grouping_period]
    except KeyError:
        raise ValueError(f"grouping_period must be 'all_data', 'fifteen_min', 'hour', 'day', or 'month'")

    with create_db_connection() as connection, connection.cursor(dictionary=True) as cursor:
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
    
    return rows

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
    
    try:
        rows = get_data(columns, device, start_date, end_date, grouping_period)
    except Exception as e:
        logging.exception("failed to obtain data")
        return jsonify({"error": str(e)}), 400

    return jsonify(rows), 200

if __name__ == '__main__':
    app.run(host="0.0.0.0", debug=False)
