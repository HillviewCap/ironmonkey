#!/bin/bash

# Read MongoDB credentials from secret files
MONGO_USER=$(cat /run/secrets/mongodb_auth | grep MONGO_INITDB_ROOT_USERNAME | cut -d= -f2)
MONGO_PASSWORD=$(cat /run/secrets/mongodb_auth | grep MONGO_INITDB_ROOT_PASSWORD | cut -d= -f2)

# Construct MONGO_URI
export MONGO_URI="mongodb://${MONGO_USER}:${MONGO_PASSWORD}@mongodb:27017/${MONGO_DATABASE}"

# Start your application
python your_app.py
