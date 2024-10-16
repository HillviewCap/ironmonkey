from flask import Flask, render_template, request, jsonify
import sqlite3
import requests
import os

app = Flask(__name__)

# SQLite database connection
def get_db_connection():
    db_path = os.path.join('instance', 'threats.db')
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    return conn

# Route for the home page
@app.route('/')
def index():
    return render_template('index.html')

# Route to fetch data from SQLite
@app.route('/get_data')
def get_data():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT name FROM sqlite_master WHERE type="table"')
    tables = cursor.fetchall()
    
    data = {}
    for table in tables:
        cursor.execute(f'SELECT * FROM {table[0]} LIMIT 5')
        data[table[0]] = [dict(ix) for ix in cursor.fetchall()]
    
    conn.close()
    return jsonify(data)

# Route to send data to the back-end service
@app.route('/send_to_backend', methods=['POST'])
def send_to_backend():
    data = request.json
    response = requests.post('http://sync_service:8000/receive_data', json=data)
    return jsonify(response.json())

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0')
