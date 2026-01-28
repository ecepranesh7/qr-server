from flask import Flask, jsonify
import os, json, threading, time
import cv2
from pyzbar.pyzbar import decode
import firebase_admin
from firebase_admin import credentials, db

app = Flask(__name__)

latest = {"qr": None, "status": "WAITING"}

# ---------- Firebase ----------
service_account_json = os.environ.get("FIREBASE_SERVICE_ACCOUNT")
database_url = os.environ.get("FIREBASE_DB_URL")

cred = credentials.Certificate(json.loads(service_account_json))
firebase_admin.initialize_app(cred, {"databaseURL": database_url})

STREAM_URL = os.environ.get("ESP32_STREAM_URL")

def scanner():
    global latest
    while True:
        try:
            cap = cv2.VideoCapture(STREAM_URL)
            if not cap.isOpened():
                time.sleep(5)
                continue

            while True:
                ret, frame = cap.read()
                if not ret:
                    break

                for q in decode(frame):
                    qr = q.data.decode()
                    valid = db.reference(f"/authorized_qr/{qr}").get() == True
                    status = "VALID" if valid else "INVALID"
                    latest = {"qr": qr, "status": status}
                    time.sleep(2)

        except Exception as e:
            print("Scanner error:", e)
            time.sleep(5)

@app.route("/")
def home():
    return "QR Server is running"

@app.route("/result")
def result():
    return jsonify(latest)

if __name__ == "__main__":
    threading.Thread(target=scanner, daemon=True).start()
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
