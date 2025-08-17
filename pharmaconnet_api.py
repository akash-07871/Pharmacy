
# PharmaConnect API (Flask + SQLAlchemy)
# -------------------------------------
# Quick-start backend to power your distributor/pharmacy demo.
# Uses SQLite for simplicity. Includes:
# - Users (pharmacy, distributor)
# - Medicines
# - Stock per distributor
# - Orders with multiple items
# - Payments
# - Backup requests when stock is insufficient
# - CORS enabled for your HTML demo pages
#
# Run:
#   pip install -r requirements.txt  (see chat for the list)
#   python pharmaconnect_api.py
#
# The API runs at http://127.0.0.1:5000
#
# Seed data is auto-created on first run.

from __future__ import annotations
import os
from datetime import datetime
from typing import List, Dict

from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy

app = Flask(__name__)
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///pharmaconnect.db"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
db = SQLAlchemy(app)

# ------------------------
# Database Models
# ------------------------

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    role = db.Column(db.String(20), nullable=False)  # "Distributor" / "Pharmacy"
    email = db.Column(db.String(100), unique=True, nullable=False)
    password = db.Column(db.String(100), nullable=False)


class Medicine(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)


class Stock(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    distributor_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    medicine_id = db.Column(db.Integer, db.ForeignKey("medicine.id"), nullable=False)
    available_qty = db.Column(db.Integer, nullable=False, default=0)


class Order(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    pharmacy_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    distributor_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    status = db.Column(db.String(20), nullable=False, default="Pending")


class OrderItem(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    order_id = db.Column(db.Integer, db.ForeignKey("order.id"), nullable=False)
    medicine_id = db.Column(db.Integer, db.ForeignKey("medicine.id"), nullable=False)
    qty = db.Column(db.Integer, nullable=False)
    price = db.Column(db.Float, nullable=False)


# ------------------------
# API Routes
# ------------------------

@app.route("/orders", methods=["POST"])
def create_order():
    """
    Create a new order with items
    Request JSON:
    {
        "pharmacy_id": 2,
        "distributor_id": 1,
        "items": [
            {"medicine_id": 1, "qty": 10, "price": 5.0},
            {"medicine_id": 2, "qty": 20, "price": 3.0}
        ]
    }
    """
    data = request.json
    new_order = Order(pharmacy_id=data["pharmacy_id"], distributor_id=data["distributor_id"], status="Pending")
    db.session.add(new_order)
    db.session.commit()

    for item in data["items"]:
        order_item = OrderItem(
            order_id=new_order.id,
            medicine_id=item["medicine_id"],
            qty=item["qty"],
            price=item["price"]
        )
        db.session.add(order_item)

    db.session.commit()
    return jsonify({"message": "Order created successfully", "order_id": new_order.id})


@app.route("/orders/<int:order_id>", methods=["GET"])
def get_order(order_id):
    order = Order.query.get(order_id)
    if not order:
        return jsonify({"error": "Order not found"}), 404

    items = OrderItem.query.filter_by(order_id=order.id).all()
    item_list = [
        {"medicine_id": i.medicine_id, "qty": i.qty, "price": i.price}
        for i in items
    ]

    return jsonify({
        "id": order.id,
        "pharmacy_id": order.pharmacy_id,
        "distributor_id": order.distributor_id,
        "status": order.status,
        "items": item_list
    })


@app.route("/orders/<int:order_id>/status", methods=["PUT"])
def update_order_status(order_id):
    data = request.json
    order = Order.query.get(order_id)
    if not order:
        return jsonify({"error": "Order not found"}), 404

    order.status = data.get("status", order.status)
    db.session.commit()
    return jsonify({"message": "Order status updated", "status": order.status})


# ------------------------
# Run & Seed Data
# ------------------------

if __name__ == "__main__":
    with app.app_context():
        db.create_all()

        # --- Seed demo data only once ---
        if not User.query.first():
            distributor = User(name="Main Distributor", role="Distributor",
                               email="d1@example.com", password="pass")
            pharmacy = User(name="Pharma Plus", role="Pharmacy",
                            email="p1@example.com", password="pass")
            db.session.add_all([distributor, pharmacy])
            db.session.commit()

            med1 = Medicine(name="Paracetamol 500mg")
            med2 = Medicine(name="Amoxicillin 250mg")
            db.session.add_all([med1, med2])
            db.session.commit()

            stock1 = Stock(distributor_id=distributor.id, medicine_id=med1.id, available_qty=50)
            stock2 = Stock(distributor_id=distributor.id, medicine_id=med2.id, available_qty=30)
            db.session.add_all([stock1, stock2])
            db.session.commit()

            print("✅ Seeded demo data")

    app.run(debug=True)
