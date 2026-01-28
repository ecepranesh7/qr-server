import cv2
from flask import Flask, jsonify
import firebase_admin
from firebase_admin import credentials, db
import os, json, threading, time

# ---------- Firebase ----------
service_account_json = os.environ["FIREBASE_SERVICE_ACCOUNT"]
database_url = os.environ["FIREBASE_DB_URL"]

cred = credentials.Certificate(json.loads(service_account_json))
firebase_admin.initialize_app(cred, {"databaseURL": database_url})

# ---------- Stream URL ----------
STREAM_URL = os.environ["ESP32_STREAM_URL"]

app = Flask(__name__)
latest = {"qr": None, "status": "WAITING"}

detector = cv2.QRCodeDetector()

def scanner():
    global latest
    while True:
        try:
            print("Connecting to stream...")
            cap = cv2.VideoCapture(STREAM_URL)

            if not cap.isOpened():
                print("Stream open failed, retrying...")
                time.sleep(5)
                continue

            while True:
                ret, frame = cap.read()
                if not ret:
                    break

                data, bbox, _ = detector.detectAndDecode(frame)

                if data:
                    print("QR detected:", data)

                    valid = db.reference(f"/authorized_qr/{data}").get() == True
                    status = "VALID" if valid else "INVALID"

                    latest = {"qr": data, "status": status}

                    db.reference("/scan_logs").push({
                        "qr": data,
                        "status": status,
                        "time": int(time.time())
                    })

                    time.sleep(2)

        except Exception as e:
            print("Scanner error:", e)
            time.sleep(5)

@app.route("/")
def home():
    return "QR Server Running"

@app.route("/result")
def result():
    return jsonify(latest)

if __name__ == "__main__":
    threading.Thread(target=scanner, daemon=True).start()
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
