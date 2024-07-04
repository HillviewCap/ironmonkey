from flask import Flask, render_template, request
import sqlite3

app = Flask(__name__)

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/search')
def search():
    query = request.args.get('query', '')
    # TODO: Implement actual database search
    results = [f"Dummy result for '{query}'"]
    return render_template('search_results.html', results=results)

if __name__ == '__main__':
    app.run(debug=True)
