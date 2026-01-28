import cv2
from pyzbar.pyzbar import decode
from flask import Flask, request, jsonify
import firebase_admin
from firebase_admin import credentials, db
import os, json, threading, time

# -----------------------------
# Firebase Init from ENV
# -----------------------------
service_account_json = os.environ.get("FIREBASE_SERVICE_ACCOUNT")
database_url = os.environ.get("FIREBASE_DB_URL")

cred = credentials.Certificate(json.loads(service_account_json))
firebase_admin.initialize_app(cred, {
    "databaseURL": database_url
})

# -----------------------------
# Flask App
# -----------------------------
app = Flask(__name__)

latest_result = {
    "qr": None,
    "status": "WAITING"
}

# -----------------------------
# QR Scanner Thread
# -----------------------------
ESP32_STREAM_URL = os.environ.get("ESP32_STREAM_URL")

def qr_scanner():
    global latest_result

    while True:
        try:
            print("Connecting to ESP32 stream...")
            cap = cv2.VideoCapture(ESP32_STREAM_URL)

            if not cap.isOpened():
                print("Stream open failed. Retrying...")
                time.sleep(5)
                continue

            while True:
                ret, frame = cap.read()
                if not ret:
                    break

                decoded = decode(frame)

                for qr in decoded:
                    qr_text = qr.data.decode("utf-8")

                    print("QR Detected:", qr_text)

                    ref = db.reference(f"/authorized_qr/{qr_text}")
                    valid = ref.get() == True

                    status = "VALID" if valid else "INVALID"

                    latest_result = {
                        "qr": qr_text,
                        "status": status
                    }

                    db.reference("/scan_logs").push({
                        "qr": qr_text,
                        "status": status,
                        "time": int(time.time())
                    })

                    time.sleep(2)

        except Exception as e:
            print("Error:", e)
            time.sleep(5)

# -----------------------------
# API Endpoint
# -----------------------------
@app.route("/")
def home():
    return "ESP32 QR Server Running"

@app.route("/result")
def result():
    return jsonify(latest_result)

# -----------------------------
# Start
# -----------------------------
if __name__ == "__main__":
    t = threading.Thread(target=qr_scanner, daemon=True)
    t.start()

    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
