from flask import Flask, render_template, request, redirect, session, jsonify
from flask_sqlalchemy import SQLAlchemy
import random, string

app = Flask(__name__)
app.secret_key = "super_secret_key"
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///pharma.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

# ------------------ MODELS ------------------
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(100), unique=True, nullable=False)
    password = db.Column(db.String(100))  # for distributor and backup
    role = db.Column(db.String(20), nullable=False)
    secret_code = db.Column(db.String(20))  # for pharmacy login
    linked_distributor_id = db.Column(db.Integer)  # link pharmacy to distributor

# ------------------ ROUTES ------------------
@app.route("/", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        role = request.form["role"]
        username = request.form["username"].lower()
        password = request.form.get("password")
        secret_code = request.form.get("secret_code")

        if role == "pharmacy":
            # Get pharmacy by username
            pharmacy = User.query.filter_by(username=username, role="pharmacy").first()
            if pharmacy and pharmacy.linked_distributor_id:
                # Get linked distributor
                distributor = User.query.get(pharmacy.linked_distributor_id)
                if distributor and distributor.secret_code == secret_code:
                    # Login successful
                    session["username"] = pharmacy.username
                    session["role"] = pharmacy.role
                    return redirect("/pharmacy")
            # Invalid credentials
            return render_template("login.html", error="Invalid credentials!")

        else:  # distributor or backup
            user = User.query.filter_by(username=username, password=password, role=role).first()
            if user:
                session["username"] = user.username
                session["role"] = user.role
                if role == "distributor":
                    return redirect("/distributor")
                elif role == "backup":
                    return redirect("/backup")
            else:
                return render_template("login.html", error="Invalid credentials!")

    return render_template("login.html")


@app.route("/distributor")
def distributor_dashboard():
    if session.get("role") != "distributor":
        return redirect("/")
    return render_template("distributor.html")

@app.route("/pharmacy")
def pharmacy_dashboard():
    if session.get("role") != "pharmacy":
        return redirect("/")
    return render_template("pharmacy.html")

# ------------------ GENERATE SECRET CODE ------------------
@app.route("/generate_distributor_code", methods=["POST"])
def generate_distributor_code():
    distributor_username = session.get("username")
    if not distributor_username or session.get("role") != "distributor":
        return {"error": "Unauthorized"}, 401

    distributor = User.query.filter_by(username=distributor_username, role="distributor").first()
    if not distributor:
        return {"error": "Distributor not found"}, 404

    # Generate unique 6-char code
    code = ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))
    distributor.secret_code = code
    db.session.commit()
    return {"code": code}

# ------------------ INIT ------------------
if __name__ == "__main__":
    with app.app_context():
        db.create_all()

        # Sample users if database empty
        if not User.query.first():
            distributor = User(username="distributor", password="123", role="distributor")
            # Link pharmacy to distributor using distributor.id after commit
            db.session.add(distributor)
            db.session.commit()

            pharmacy = User(username="pharmacy", role="pharmacy", linked_distributor_id=distributor.id)
            backup = User(username="backup", password="123", role="backup")
            db.session.add_all([pharmacy, backup])
            db.session.commit()

    app.run(debug=True)
