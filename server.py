import os
import json
import firebase_admin
from firebase_admin import credentials, db
from flask import Flask, request, jsonify
import time

# Read Firebase Service Account JSON from environment variable
FIREBASE_SERVICE_ACCOUNT = os.environ.get("FIREBASE_SERVICE_ACCOUNT")
FIREBASE_DB_URL = os.environ.get("FIREBASE_DB_URL")

if not FIREBASE_SERVICE_ACCOUNT or not FIREBASE_DB_URL:
    raise Exception("Environment variables FIREBASE_SERVICE_ACCOUNT and FIREBASE_DB_URL must be set!")

# Convert JSON string to dictionary
service_account_info = json.loads(FIREBASE_SERVICE_ACCOUNT)

# Initialize Firebase
cred = credentials.Certificate(service_account_info)
firebase_admin.initialize_app(cred, {
    "databaseURL": FIREBASE_DB_URL
})

app = Flask(__name__)
