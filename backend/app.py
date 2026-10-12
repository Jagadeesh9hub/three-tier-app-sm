
from decimal import Decimal, InvalidOperation
from flask import Flask, jsonify, request
from db import get_connection

app = Flask(__name__)


@app.get("/api/health")
def health():
    return jsonify({"status": "healthy", "service": "backend"})


@app.get("/api/products")
def get_products():
    try:
        conn = get_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute(
            "SELECT id, name, price FROM products ORDER BY id DESC"
        )
        products = cursor.fetchall()
        cursor.close()
        conn.close()

        for product in products:
            product["price"] = str(product["price"])

        return jsonify(products)
    except Exception:
        app.logger.exception("Unable to retrieve products")
        return jsonify({"error": "Unable to retrieve products"}), 500


@app.post("/api/products")
def create_product():
    data = request.get_json(silent=True)

    if not isinstance(data, dict):
        return jsonify({"error": "JSON body required"}), 400

    name = data.get("name")
    if not isinstance(name, str) or not name.strip():
        return jsonify({"error": "Product name is required"}), 400

    name = name.strip()
    if len(name) > 100:
        return jsonify({"error": "Name must be 100 characters or less"}), 400

    try:
        price = Decimal(str(data.get("price")))
        if not price.is_finite() or price <= 0 or price > Decimal("99999999.99"):
            raise InvalidOperation
        price = price.quantize(Decimal("0.01"))
    except (InvalidOperation, ValueError, TypeError):
        return jsonify({"error": "Enter a valid positive price"}), 400

    conn = None
    cursor = None
    try:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO products (name, price) VALUES (%s, %s)",
            (name, price),
        )
        conn.commit()
        return jsonify({
            "id": cursor.lastrowid,
            "name": name,
            "price": str(price),
        }), 201
    except Exception:
        if conn is not None:
            conn.rollback()
        app.logger.exception("Unable to create product")
        return jsonify({"error": "Unable to save product"}), 500
    finally:
        if cursor is not None:
            cursor.close()
        if conn is not None:
            conn.close()
