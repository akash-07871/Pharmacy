from flask import Flask, jsonify, request
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS

app = Flask(__name__)
CORS(app)  # allow frontend to call backend (important!)

# Configure database (SQLite for now)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///pharma.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

# ------------------- MODELS -------------------
class Stock(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    medicine = db.Column(db.String(100), nullable=False)
    qty = db.Column(db.Integer, nullable=False)

class Order(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    pharmacy = db.Column(db.String(100), nullable=False)
    medicine = db.Column(db.String(100), nullable=False)
    qty = db.Column(db.Integer, nullable=False)
    status = db.Column(db.String(20), default="Pending")

# ------------------- ROUTES -------------------
@app.route("/stock", methods=["GET"])
def get_stock():
    stock = Stock.query.all()
    return jsonify([{"medicine": s.medicine, "qty": s.qty} for s in stock])

@app.route("/orders", methods=["GET"])
def get_orders():
    orders = Order.query.all()
    return jsonify([
        {"pharmacy": o.pharmacy, "medicine": o.medicine, "qty": o.qty, "status": o.status}
        for o in orders
    ])

@app.route("/orders", methods=["POST"])
def add_order():
    data = request.json
    new_order = Order(
        pharmacy=data["pharmacy"],
        medicine=data["medicine"],
        qty=data["qty"],
        status="Pending"
    )
    db.session.add(new_order)
    db.session.commit()
    return jsonify({"message": "Order placed successfully"}), 201

# ------------------- MAIN -------------------
if __name__ == "__main__":
    with app.app_context():  # ✅ fixes application context error
        db.create_all()
        # Insert sample stock if empty
        if not Stock.query.first():
            db.session.add_all([
                Stock(medicine="Paracetamol 500mg", qty=25),
                Stock(medicine="Amoxicillin 250mg", qty=0),
                Stock(medicine="Ibuprofen 400mg", qty=40),
                Stock(medicine="Vitamin C Tablets", qty=10),
                Stock(medicine="Azithromycin 500mg", qty=10),
            ])
            db.session.commit()
    app.run(debug=True)
