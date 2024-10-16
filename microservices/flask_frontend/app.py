from flask import Flask, render_template, request, jsonify
import sqlite3
import requests

app = Flask(__name__)

# SQLite database connection
def get_db_connection():
    conn = sqlite3.connect('database.db')
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
    cursor.execute('SELECT * FROM your_table')
    data = cursor.fetchall()
    conn.close()
    return jsonify([dict(ix) for ix in data])

# Route to send data to the back-end service
@app.route('/send_to_backend', methods=['POST'])
def send_to_backend():
    data = request.json
    # Assuming your back-end service is running on localhost:5000
    response = requests.post('http://sync_service:5000/receive_data', json=data)
    return jsonify(response.json())

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0')
