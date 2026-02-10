import os, json
from flask import Flask, request, jsonify
from dotenv import load_dotenv
from uuid import uuid4
from datetime import datetime

load_dotenv()

app = Flask(__name__)

PORT = int(os.getenv("PORT", "5000"))
API_KEY = os.getenv("API_KEY")
DATA_FILE = os.getenv("DATA_FILE", "./data/db.json")
BEARER_TOKEN = os.getenv("BEARER_TOKEN")
BASIC_USER = os.getenv("BASIC_USER")
BASIC_PASS = os.getenv("BASIC_PASS")

def require_basic_auth():
    auth = request.authorization
    if not auth:
        return jsonify({"error": "Unauthorized: missing credentials"}), 401

    if auth.username != BASIC_USER or auth.password != BASIC_PASS:
        return jsonify({"error": "Unauthorized: invalid username or password"}), 401

    return None


def now():
    return datetime.utcnow().isoformat() + "Z"

def ensure_db():
    os.makedirs(os.path.dirname(DATA_FILE), exist_ok=True)
    if not os.path.exists(DATA_FILE):
        with open(DATA_FILE, "w", encoding="utf-8") as f:
            json.dump({"products": [], "orders": []}, f, indent=2)

def read_db():
    ensure_db()
    with open(DATA_FILE, "r", encoding="utf-8") as f:
        return json.load(f)

def write_db(db):
    ensure_db()
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(db, f, indent=2)

def require_api_key():
    if not API_KEY:
        return jsonify({"error": "Server misconfigured: API_KEY missing"}), 500
    provided = request.headers.get("x-api-key")
    if not provided or provided != API_KEY:
        return jsonify({"error": "Unauthorized: invalid or missing API key"}), 401
    return None

@app.get("/health")
def health():
    return jsonify({"status": "ok", "time": now()})

@app.before_request
def auth_guard():
    if request.path.startswith("/api"):
        if require_api_key() is None:
            return None

        if require_bearer_token() is None:
            return None

        if require_basic_auth() is None:
            return None

        return jsonify({"error": "Unauthorized"}), 401

# -------- Products --------
@app.get("/api/products")
def list_products():
    db = read_db()
    return jsonify(db["products"])

@app.get("/api/products/<pid>")
def get_product(pid):
    db = read_db()
    for p in db["products"]:
        if p["id"] == pid:
            return jsonify(p)
    return jsonify({"error": "Product not found"}), 404

@app.post("/api/products")
def create_product():
    payload = request.get_json(silent=True) or {}
    name = payload.get("name")
    price = payload.get("price")
    if not name or price is None:
        return jsonify({"error": "name and price are required"}), 400
    db = read_db()
    created = {"id": str(uuid4()), "name": name, "price": price, "createdAt": now()}
    db["products"].append(created)
    write_db(db)
    return jsonify(created), 201

@app.put("/api/products/<pid>")
def update_product(pid):
    payload = request.get_json(silent=True) or {}
    db = read_db()
    for i, p in enumerate(db["products"]):
        if p["id"] == pid:
            p["name"] = payload.get("name", p["name"])
            if "price" in payload:
                p["price"] = payload["price"]
            p["updatedAt"] = now()
            db["products"][i] = p
            write_db(db)
            return jsonify(p)
    return jsonify({"error": "Product not found"}), 404

@app.delete("/api/products/<pid>")
def delete_product(pid):
    db = read_db()
    before = len(db["products"])
    db["products"] = [p for p in db["products"] if p["id"] != pid]
    if len(db["products"]) == before:
        return jsonify({"error": "Product not found"}), 404
    write_db(db)
    return ("", 204)

# -------- Orders --------
@app.get("/api/orders")
def list_orders():
    db = read_db()
    return jsonify(db["orders"])

@app.get("/api/orders/<oid>")
def get_order(oid):
    db = read_db()
    for o in db["orders"]:
        if o["id"] == oid:
            return jsonify(o)
    return jsonify({"error": "Order not found"}), 404

@app.post("/api/orders")
def create_order():
    payload = request.get_json(silent=True) or {}
    customer = payload.get("customer")
    items = payload.get("items", [])
    if not customer or not isinstance(items, list):
        return jsonify({"error": "customer and items[] are required"}), 400

    db = read_db()
    created = {
        "id": str(uuid4()),
        "customer": customer,
        "items": items,
        "status": payload.get("status", "NEW"),
        "createdAt": now()
    }
    db["orders"].append(created)
    write_db(db)
    return jsonify(created), 201

@app.put("/api/orders/<oid>")
def update_order(oid):
    payload = request.get_json(silent=True) or {}
    db = read_db()
    for i, o in enumerate(db["orders"]):
        if o["id"] == oid:
            o["customer"] = payload.get("customer", o["customer"])
            if "items" in payload:
                o["items"] = payload["items"]
            o["status"] = payload.get("status", o["status"])
            o["updatedAt"] = now()
            db["orders"][i] = o
            write_db(db)
            return jsonify(o)
    return jsonify({"error": "Order not found"}), 404

@app.delete("/api/orders/<oid>")
def delete_order(oid):
    db = read_db()
    before = len(db["orders"])
    db["orders"] = [o for o in db["orders"] if o["id"] != oid]
    if len(db["orders"]) == before:
        return jsonify({"error": "Order not found"}), 404
    write_db(db)
    return ("", 204)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=PORT)
