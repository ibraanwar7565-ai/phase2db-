import base64
import os
import secrets
from datetime import datetime, timezone
import requests
from flask import Blueprint, request, jsonify
from sqlalchemy.exc import IntegrityError
from errors import api_error
from extensions import db
from models import Budget, Transaction, User, MAX_TRANSACTION_CENTS
from utils import is_int, normalize_kenyan_phone

mpesa_bp = Blueprint("mpesa", __name__, url_prefix="/api/mpesa")

# In-memory stores: fine for a single-process demo, lost on restart.
PENDING = {}   # checkout_request_id -> what the user asked to pay
RESULTS = {}   # checkout_request_id -> final status, for the frontend to poll


def env(name, default=""):
    # Read lazily: .env is loaded when config.py is imported, after this module.
    return os.environ.get(name, default)


def get_access_token():
    """Daraja OAuth: consumer key/secret -> short-lived bearer token."""
    resp = requests.get(
        f"{env('MPESA_BASE_URL', 'https://sandbox.safaricom.co.ke')}/oauth/v1/generate",
        params={"grant_type": "client_credentials"},
        auth=(env("MPESA_CONSUMER_KEY"), env("MPESA_CONSUMER_SECRET")),
        timeout=15,
    )
    resp.raise_for_status()
    return resp.json()["access_token"]


def send_stk_push(phone, amount_shillings, reference, description):
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%d%H%M%S")
    shortcode = env("MPESA_SHORTCODE")
    password = base64.b64encode(
        f"{shortcode}{env('MPESA_PASSKEY')}{timestamp}".encode()
    ).decode()

    resp = requests.post(
        f"{env('MPESA_BASE_URL', 'https://sandbox.safaricom.co.ke')}/mpesa/stkpush/v1/processrequest",
        headers={"Authorization": f"Bearer {get_access_token()}"},
        json={
            "BusinessShortCode": shortcode,
            "Password": password,
            "Timestamp": timestamp,
            "TransactionType": "CustomerPayBillOnline",
            "Amount": amount_shillings,
            "PartyA": phone,
            "PartyB": shortcode,
            "PhoneNumber": phone,
            "CallBackURL": env("MPESA_CALLBACK_URL"),
            "AccountReference": reference[:12],
            "TransactionDesc": description[:13],
        },
        timeout=20,
    )
    return resp.json()


def process_callback(payload):
    """Shared by the real Daraja callback and the simulator. Returns a status string."""
    cb = (payload.get("Body") or {}).get("stkCallback") or {}
    checkout_id = cb.get("CheckoutRequestID")
    pending = PENDING.pop(checkout_id, None)
    if pending is None:
        return "unknown"

    if cb.get("ResultCode") != 0:
        RESULTS[checkout_id] = {"status": "failed", "message": cb.get("ResultDesc")}
        return "failed"

    items = {i.get("Name"): i.get("Value")
             for i in (cb.get("CallbackMetadata") or {}).get("Item", [])}
    transaction = Transaction(
        user_id=pending["user_id"],
        budget_id=pending["budget_id"],
        description=pending["description"],
        amount_cents=pending["amount_cents"],
        transaction_type="paybill",
        mpesa_code=items.get("MpesaReceiptNumber"),
    )
    try:
        db.session.add(transaction)
        db.session.commit()
    except IntegrityError:          # Safaricom retried a callback we already saved
        db.session.rollback()
        RESULTS[checkout_id] = {"status": "completed", "message": "Already recorded"}
        return "duplicate"

    RESULTS[checkout_id] = {"status": "completed",
                            "transaction": transaction.to_dict()}
    return "completed"


@mpesa_bp.route("/stkpush", methods=["POST"])
def stk_push():
    data = request.get_json(silent=True)
    if not isinstance(data, dict):
        return api_error(400, "bad_request", "Request body must be valid JSON")

    user_id = data.get("user_id")
    budget_id = data.get("budget_id")
    amount_cents = data.get("amount_cents")
    description = data.get("description") or "M-Pesa payment"

    if not is_int(user_id) or user_id <= 0:
        return api_error(400, "validation_error", "A valid user_id is required")
    user = db.session.get(User, user_id)
    if user is None:
        return api_error(404, "not_found", "User not found")

    phone = normalize_kenyan_phone(data.get("phone") or user.phone)
    if phone is None:
        return api_error(400, "validation_error",
                         "A valid Kenyan phone number is required, e.g. 0712345678")

    if (not is_int(amount_cents) or amount_cents < 100
            or amount_cents > MAX_TRANSACTION_CENTS or amount_cents % 100):
        return api_error(400, "validation_error",
                         "amount_cents must be whole shillings (a multiple of 100), at least 100")

    if not isinstance(description, str) or len(description.strip()) > 200:
        return api_error(400, "validation_error", "description must be at most 200 characters")
    description = description.strip() or "M-Pesa payment"

    if budget_id is not None:
        if not is_int(budget_id) or budget_id <= 0:
            return api_error(400, "validation_error", "Invalid budget_id")
        budget = db.session.get(Budget, budget_id)
        if budget is None or budget.user_id != user_id:
            return api_error(404, "not_found", "Budget does not exist for this user")

    pending = {"user_id": user_id, "budget_id": budget_id,
               "amount_cents": amount_cents, "description": description}

    # --- Simulate mode: no Safaricom needed ---
    if env("MPESA_MODE", "simulate") == "simulate":
        checkout_id = "ws_CO_SIM_" + secrets.token_hex(6)
        PENDING[checkout_id] = pending
        status = process_callback({"Body": {"stkCallback": {
            "CheckoutRequestID": checkout_id, "ResultCode": 0,
            "ResultDesc": "The service request is processed successfully.",
            "CallbackMetadata": {"Item": [
                {"Name": "MpesaReceiptNumber", "Value": "SIM" + secrets.token_hex(4).upper()},
                {"Name": "PhoneNumber", "Value": int(phone)},
            ]},
        }}})
        return jsonify({"mode": "simulate", "checkout_request_id": checkout_id,
                        "status": status, "result": RESULTS.get(checkout_id)}), 200

    # --- Real Daraja sandbox ---
    try:
        reply = send_stk_push(phone, amount_cents // 100, "SmartPesa", description)
    except (requests.RequestException, KeyError, ValueError):
        return api_error(502, "mpesa_unavailable",
                         "Could not reach M-Pesa. Check credentials and network.")

    if reply.get("ResponseCode") != "0":
        return api_error(502, "mpesa_rejected",
                         reply.get("errorMessage") or reply.get("ResponseDescription")
                         or "M-Pesa rejected the request")

    checkout_id = reply["CheckoutRequestID"]
    PENDING[checkout_id] = pending
    RESULTS[checkout_id] = {"status": "pending"}
    return jsonify({"mode": "daraja", "checkout_request_id": checkout_id,
                    "status": "pending",
                    "message": "Check your phone and enter your M-Pesa PIN"}), 202


@mpesa_bp.route("/callback", methods=["POST"])
def callback():
    """Safaricom (or you, via curl) posts the payment result here."""
    payload = request.get_json(silent=True)
    if isinstance(payload, dict):
        process_callback(payload)
    # Always acknowledge, or Safaricom keeps retrying.
    return jsonify({"ResultCode": 0, "ResultDesc": "Accepted"}), 200


@mpesa_bp.route("/status/<checkout_id>", methods=["GET"])
def status(checkout_id):
    result = RESULTS.get(checkout_id)
    if result is None:
        return api_error(404, "not_found", "Unknown checkout request")
    return jsonify(result), 200