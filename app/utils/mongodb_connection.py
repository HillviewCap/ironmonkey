from pymongo import MongoClient
from flask import current_app

def get_mongo_client():
    mongodb_uri = current_app.config['MONGODB_URI']
    return MongoClient(mongodb_uri)
