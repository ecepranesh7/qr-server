from flask import Flask, request, jsonify
import firebase_admin
from firebase_admin import credentials, db
import time
import os
import json

# ---------- Read env variables ----------
FIREBASE_DB_URL = os.environ.get("FIREBASE_DB_URL")
FIREBASE_SERVICE_ACCOUNT = os.environ.get("FIREBASE_SERVICE_ACCOUNT")

# Convert JSON string to dict
service_account_info = json.loads(FIREBASE_SERVICE_ACCOUNT)

# Firebase init
cred = credentials.Certificate(service_account_info)
firebase_admin.initialize_app(cred, {
    "databaseURL": FIREBASE_DB_URL
})

app = Flask(__name__)

@app.route("/")
def home():
    return "QR Validation Server Running"

@app.route("/check_qr", methods=["GET"])
def check_qr():
    qr = request.args.get("qr")

    if not qr:
        return jsonify({"error": "QR missing"}), 400

    ref = db.reference(f"authorized_qr/{qr}")
    value = ref.get()

    status = "VALID" if value == True else "INVALID"

    db.reference("scan_result").set({
        "qr": qr,
        "status": status,
        "time": time.strftime("%Y-%m-%d %H:%M:%S")
    })

    return jsonify({"qr": qr, "status": status})

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
