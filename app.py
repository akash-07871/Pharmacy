from flask import Flask, render_template, request, redirect, session
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
    password = db.Column(db.String(100))
    role = db.Column(db.String(20), nullable=False)
    secret_code = db.Column(db.String(20))
    linked_distributor_id = db.Column(db.Integer)

# ------------------ ROUTES ------------------
@app.route("/", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        role = request.form["role"]
        username = request.form["username"].lower()
        password = request.form.get("password")

        # Distributor / Backup login
        if role in ["distributor", "backup"]:
            user = User.query.filter_by(username=username, password=password, role=role).first()
            if user:
                session["username"] = user.username
                session["role"] = user.role
                if role == "distributor":
                    return redirect("/distributor")
                else:
                    return redirect("/backup")
            return render_template("login.html", error="Invalid credentials!")

        # Pharmacy login
        elif role == "pharmacy":
            user = User.query.filter_by(username=username, password=password, role="pharmacy").first()
            if user:
                session["username"] = user.username
                session["role"] = user.role
                return redirect("/pharmacy")
            return render_template("login.html", error="Invalid credentials!")

    return render_template("login.html")


@app.route("/distributor")
def distributor_dashboard():
    if session.get("role") != "distributor":
        return redirect("/")
    
    distributor = User.query.filter_by(username=session["username"], role="distributor").first()
    return render_template("distributor_dashboard.html", distributor=distributor)


@app.route("/pharmacy")
def pharmacy_dashboard():
    if session.get("role") != "pharmacy":
        return redirect("/")
    return render_template("pharmacy_dashboard.html", username=session["username"])


@app.route("/pharmacy_register/<invite_code>")
def pharmacy_register(invite_code):
    distributor = User.query.filter_by(secret_code=invite_code, role="distributor").first()
    if not distributor:
        return "Invalid or expired invite link", 400
    
    return render_template("pharmacy_register.html", distributor=distributor, invite_code=invite_code)



@app.route("/pharmacy_register_submit", methods=["POST"])
def pharmacy_register_submit():
    username = request.form["username"]
    password = request.form["password"]
    invite_code = request.form["invite_code"]

    # Find distributor by invite code
    distributor = User.query.filter_by(secret_code=invite_code, role="distributor").first()
    if not distributor:
        return "Invalid invite code", 400

    # Check if pharmacy username already exists
    existing_user = User.query.filter_by(username=username).first()
    if existing_user:
        return "Username already taken", 400

    # Create new pharmacy linked to distributor
    pharmacy = User(
        username=username,
        password=password,
        role="pharmacy",
        linked_distributor_id=distributor.id
    )
    db.session.add(pharmacy)
    db.session.commit()

    return f"Pharmacy {username} registered successfully under Distributor {distributor.username}! <a href='/'>Login</a>"



@app.route("/logout")
def logout():
    session.clear()
    return redirect("/")


# ------------------ INIT ------------------
if __name__ == "__main__":
    with app.app_context():
        db.create_all()

        # Sample users if database is empty
        if not User.query.first():
            distributor = User(username="distributor", password="123", role="distributor")
            pharmacy = User(username="pharmacy", password="123", role="pharmacy", linked_distributor_id=1)
            backup = User(username="backup", password="123", role="backup")
            db.session.add_all([distributor, pharmacy, backup])
            db.session.commit()

    app.run(debug=True)
