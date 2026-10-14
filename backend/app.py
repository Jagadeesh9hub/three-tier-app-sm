import os
from decimal import Decimal, InvalidOperation
from flask import Flask, jsonify, request
from flask_cors import CORS
from db import get_connection

app = Flask(__name__)
CORS(app)


def format_product(product):
    if not product:
        return None
    formatted = dict(product)
    if "price" in formatted and formatted["price"] is not None:
        formatted["price"] = str(formatted["price"])
    if "created_at" in formatted and formatted["created_at"] is not None:
        formatted["created_at"] = (
            formatted["created_at"].isoformat()
            if hasattr(formatted["created_at"], "isoformat")
            else str(formatted["created_at"])
        )
    if "updated_at" in formatted and formatted["updated_at"] is not None:
        formatted["updated_at"] = (
            formatted["updated_at"].isoformat()
            if hasattr(formatted["updated_at"], "isoformat")
            else str(formatted["updated_at"])
        )
    return formatted


@app.get("/api/health")
def health():
    return jsonify({"status": "healthy", "service": "backend"}), 200


@app.get("/api/products")
def get_products():
    category = request.args.get("category")
    conn = None
    cursor = None
    try:
        conn = get_connection()
        cursor = conn.cursor(dictionary=True)
        if category and category.strip():
            cursor.execute(
                "SELECT id, name, description, category, price, created_at, updated_at "
                "FROM products WHERE category = %s ORDER BY id DESC",
                (category.strip(),),
            )
        else:
            cursor.execute(
                "SELECT id, name, description, category, price, created_at, updated_at "
                "FROM products ORDER BY id DESC"
            )
        rows = cursor.fetchall()
        products = [format_product(row) for row in rows]
        return jsonify(products), 200
    except Exception:
        app.logger.exception("Unable to retrieve products")
        return jsonify({"error": "Unable to retrieve products"}), 500
    finally:
        if cursor is not None:
            cursor.close()
        if conn is not None:
            conn.close()


@app.get("/api/products/<int:id>")
def get_product(id):
    conn = None
    cursor = None
    try:
        conn = get_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute(
            "SELECT id, name, description, category, price, created_at, updated_at "
            "FROM products WHERE id = %s",
            (id,),
        )
        product = cursor.fetchone()
        if product is None:
            return jsonify({"error": "Product not found"}), 404
        return jsonify(format_product(product)), 200
    except Exception:
        app.logger.exception("Unable to retrieve product %s", id)
        return jsonify({"error": "Unable to retrieve product"}), 500
    finally:
        if cursor is not None:
            cursor.close()
        if conn is not None:
            conn.close()


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

    raw_price = data.get("price")
    if raw_price is None or raw_price == "":
        return jsonify({"error": "Price is required"}), 400
    try:
        price = Decimal(str(raw_price))
        if not price.is_finite() or price <= 0 or price > Decimal("99999999.99"):
            raise InvalidOperation
        price = price.quantize(Decimal("0.01"))
    except (InvalidOperation, ValueError, TypeError):
        return jsonify({"error": "Enter a valid positive price"}), 400

    description = data.get("description")
    if description is not None:
        if not isinstance(description, str):
            return jsonify({"error": "Description must be a string"}), 400
        description = description.strip()
    else:
        description = ""

    category = data.get("category")
    if category is not None:
        if not isinstance(category, str):
            return jsonify({"error": "Category must be a string"}), 400
        category = category.strip()
        if not category:
            category = "General"
        elif len(category) > 50:
            return jsonify({"error": "Category must be 50 characters or less"}), 400
    else:
        category = "General"

    conn = None
    cursor = None
    try:
        conn = get_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute(
            "INSERT INTO products (name, description, category, price) VALUES (%s, %s, %s, %s)",
            (name, description, category, price),
        )
        conn.commit()
        product_id = cursor.lastrowid

        cursor.execute(
            "SELECT id, name, description, category, price, created_at, updated_at "
            "FROM products WHERE id = %s",
            (product_id,),
        )
        created_product = cursor.fetchone()
        return jsonify(format_product(created_product)), 201
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


@app.put("/api/products/<int:id>")
def update_product(id):
    data = request.get_json(silent=True)
    if not isinstance(data, dict):
        return jsonify({"error": "JSON body required"}), 400

    conn = None
    cursor = None
    try:
        conn = get_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute(
            "SELECT id, name, description, category, price, created_at, updated_at "
            "FROM products WHERE id = %s",
            (id,),
        )
        existing = cursor.fetchone()
        if not existing:
            return jsonify({"error": "Product not found"}), 404

        name = existing["name"]
        if "name" in data:
            val = data["name"]
            if not isinstance(val, str) or not val.strip():
                return jsonify({"error": "Product name cannot be empty"}), 400
            val = val.strip()
            if len(val) > 100:
                return jsonify({"error": "Name must be 100 characters or less"}), 400
            name = val

        price = existing["price"]
        if "price" in data:
            raw_price = data["price"]
            if raw_price is None or raw_price == "":
                return jsonify({"error": "Price cannot be empty"}), 400
            try:
                val = Decimal(str(raw_price))
                if not val.is_finite() or val <= 0 or val > Decimal("99999999.99"):
                    raise InvalidOperation
                price = val.quantize(Decimal("0.01"))
            except (InvalidOperation, ValueError, TypeError):
                return jsonify({"error": "Enter a valid positive price"}), 400

        description = existing["description"]
        if "description" in data:
            val = data["description"]
            if val is not None and not isinstance(val, str):
                return jsonify({"error": "Description must be a string"}), 400
            description = val.strip() if isinstance(val, str) else ""

        category = existing["category"]
        if "category" in data:
            val = data["category"]
            if val is not None and not isinstance(val, str):
                return jsonify({"error": "Category must be a string"}), 400
            if isinstance(val, str):
                val = val.strip()
                category = val if val else "General"
            else:
                category = "General"
            if len(category) > 50:
                return jsonify({"error": "Category must be 50 characters or less"}), 400

        cursor.execute(
            "UPDATE products SET name = %s, description = %s, category = %s, price = %s "
            "WHERE id = %s",
            (name, description, category, price, id),
        )
        conn.commit()

        cursor.execute(
            "SELECT id, name, description, category, price, created_at, updated_at "
            "FROM products WHERE id = %s",
            (id,),
        )
        updated = cursor.fetchone()
        return jsonify(format_product(updated)), 200
    except Exception:
        if conn is not None:
            conn.rollback()
        app.logger.exception("Unable to update product %s", id)
        return jsonify({"error": "Unable to update product"}), 500
    finally:
        if cursor is not None:
            cursor.close()
        if conn is not None:
            conn.close()


@app.delete("/api/products/<int:id>")
def delete_product(id):
    conn = None
    cursor = None
    try:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("DELETE FROM products WHERE id = %s", (id,))
        if cursor.rowcount == 0:
            return jsonify({"error": "Product not found"}), 404
        conn.commit()
        return jsonify({"message": "Product deleted successfully", "id": id}), 200
    except Exception:
        if conn is not None:
            conn.rollback()
        app.logger.exception("Unable to delete product %s", id)
        return jsonify({"error": "Unable to delete product"}), 500
    finally:
        if cursor is not None:
            cursor.close()
        if conn is not None:
            conn.close()


@app.get("/api/categories")
def get_categories():
    conn = None
    cursor = None
    try:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute(
            "SELECT DISTINCT category FROM products "
            "WHERE category IS NOT NULL AND category != '' "
            "ORDER BY category ASC"
        )
        rows = cursor.fetchall()
        categories = [row[0] for row in rows]
        return jsonify(categories), 200
    except Exception:
        app.logger.exception("Unable to retrieve categories")
        return jsonify({"error": "Unable to retrieve categories"}), 500
    finally:
        if cursor is not None:
            cursor.close()
        if conn is not None:
            conn.close()


if __name__ == "__main__":
    port = int(os.getenv("PORT", "5000"))
    app.run(host="0.0.0.0", port=port, debug=True)
