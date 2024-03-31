import datetime
from enum import Enum
from flask import Flask, jsonify, request
from flask_cors import CORS, cross_origin
import local_options
import mysql.connector

app = Flask(__name__)
cors = CORS(app)
app.config['CORS_HEADERS'] = 'Content-Type'

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


@app.route('/data', methods=['GET'])
@cross_origin()
def query_data():
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')
    grouping_period = request.args.get('grouping_period')

    if not start_date or not end_date or not grouping_period:
        return jsonify({"error": "must specify start_date, end_date, and grouping_period"}), 400
    try:
        start_date = datetime.datetime.strptime(start_date, '%Y-%m-%d-%H')
        end_date = datetime.datetime.strptime(end_date, '%Y-%m-%d-%H')
        if start_date >= end_date:
            return jsonify({"error": "start_date must be before end_date"}), 400
    except Exception as e:
        return jsonify({"error": "Use date format YYYY-MM-DD-HH"}), 400
    try:
        time_grouping = TimeGrouping[grouping_period]
    except Exception as e:
        print(e)
        return jsonify({"error": "grouping_period must be all_data, fifteen_min, hour, day, or month"})

    connection = create_db_connection()
    cursor = connection.cursor(dictionary=True)
    if time_grouping is TimeGrouping.all_data:
        query = f"""
            SELECT
                ambient_humidity,
                ambient_light_lx,
                ambient_temp_f,
                cpu_temp_f,
                soil_moisture_level,
                soil_moisture_val,
                soil_temp_f,
                insert_time,
                device
            FROM {local_options.database_table}
            WHERE insert_time >= '{start_date}' AND insert_time < '{end_date}'
        """
    else:
        query = f"""
            SELECT
                AVG(ambient_humidity) AS ambient_humidity,
                AVG(ambient_light_lx) AS ambient_light_lx,
                AVG(ambient_temp_f) AS ambient_temp_f,
                AVG(cpu_temp_f) AS cpu_temp_f,
                AVG(soil_moisture_level) AS soil_moisture_level,
                AVG(soil_moisture_val) AS soil_moisture_val,
                AVG(soil_temp_f) AS soil_temp_f,
                {time_grouping.value} AS insert_time,
                device
            FROM {local_options.database_table}
            WHERE insert_time >= '{start_date}' AND insert_time < '{end_date}'
            GROUP BY {time_grouping.value}, device
        """
    cursor.execute(query)
    rows = cursor.fetchall()
    cursor.close()
    connection.close()
    return jsonify(rows), 200

@app.route('/test', methods=['GET'])
def test_query():
    return "big gulps huh?\n\n\n\nwhelp, see ya later!\n"

if __name__ == '__main__':
    app.run(host="0.0.0.0", debug=False)
