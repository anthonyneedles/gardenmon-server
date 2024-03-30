import datetime
from enum import Enum
from flask import Flask, jsonify, request
import local_options
import mysql.connector

app = Flask(__name__)

class TimeGrouping(Enum):
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
        print("Error while connecting to MySQL", e)
        return None


@app.route('/data', methods=['GET'])
def query_data():
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')
    grouping_period = request.args.get('grouping_period')

    if not start_date or not end_date or not grouping_period:
        return jsonify({"error": "must specify start_date, end_date, and grouping_period"}), 400
    try:
        start_date = datetime.datetime.strptime(start_date, '%Y-%m-%d')
        end_date = datetime.datetime.strptime(end_date, '%Y-%m-%d')
        if start_date >= end_date:
            return jsonify({"error": "start_date must be before end_date"}), 400
    except Exception as e:
        return jsonify({"error": "Use date format YYYY-MM-DD"}), 400
    try:
        time_grouping = TimeGrouping[grouping_period]
    except Exception as e:
        print(e)
        return jsonify({"error": "grouping_period must be hour, day, or month"})

    connection = create_db_connection()
    cursor = connection.cursor(dictionary=True)
    query = f"""
    SELECT
        avg(ambient_humidity) as avg_ambient_humidity,
        avg(ambient_light_lx) as avg_ambient_light_lx,
        avg(ambient_temp_f) as avg_ambient_temp_f,
        avg(cpu_temp_f) as avg_cpu_temp_f,
        avg(soil_moisture_level) as avg_soil_moisture_level,
        avg(soil_moisture_val) as avg_soil_moisture_val,
        avg(soil_temp_f) as avg_soil_temp_f,
        {time_grouping.value} as insert_time
    FROM {local_options.database_table}
    WHERE insert_time >= '{start_date}' and insert_time < '{end_date}'
    group by {time_grouping.value}
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
    app.run(host="127.0.0.1", debug=True)
