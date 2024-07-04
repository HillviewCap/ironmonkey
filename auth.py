from flask import Flask, redirect, url_for

app = Flask(__name__)

@app.route('/login')
def login():
    return "Logged in!"

@app.route('/index')
def index():
    return "Index page"

if __name__ == '__main__':
    app.run(debug=True)
