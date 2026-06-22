from flask import Flask, render_template, request, redirect, url_for, session, flash
import mysql.connector
import pickle
from tensorflow.keras.models import load_model
from tensorflow.keras.preprocessing.sequence import pad_sequences
import re

# ----------------------
# Flask App
# ----------------------
app = Flask(__name__)
app.secret_key = "your_secret_key"  # Replace with a strong secret key

# ----------------------
# Load CNN model and tokenizer
# ----------------------
model = load_model("model.h5")
with open("tokenizer.pkl", "rb") as f:
    tokenizer = pickle.load(f)
MAX_SEQUENCE_LENGTH = 50

# ----------------------
# MySQL Connection
# ----------------------
try:
    db = mysql.connector.connect(
        host="localhost",
        user="root",
        password="",  # <-- Put your MySQL password
        database="phishpredict_db",
        port=3306
    )
    cursor = db.cursor(buffered=True)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS email_history (
            id INT AUTO_INCREMENT PRIMARY KEY,
            email VARCHAR(255) NOT NULL,
            prediction VARCHAR(50) NOT NULL,
            confidence INT NOT NULL,
            predicted_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    db.commit()
except mysql.connector.Error as err:
    print("MySQL connection error:", err)
    cursor = None
    db = None

# ----------------------
# Suspicious keyword detection function
# ----------------------
def calculate_suspicious_score(email):
    local = email.split("@")[0].lower()
    score = 0

    # Keyword check
    keywords = ["admin", "support", "login", "secure", "update",
                "verify", "password", "bank", "account", "urgent",
                "click", "confirm","alert"]
    for kw in keywords:
        if re.search(rf"\b{kw}\b", local):
            score += 20

    # Numeric-heavy check
    if sum(c.isdigit() for c in local) > 3:
        score += 15

    # Repeated letters/numbers
    if re.search(r"(.)\1{2,}", local):
        score += 15

    # Brand impersonation
    brands = ["paypal", "bank", "amazon", "google", "apple"]
    for brand in brands:
        if brand in local:
            score += 20

    # Gibberish / very short random strings
    if len(local) <= 4:
        score += 10

    return min(score, 100)  # cap at 100

# ----------------------
# LOGIN / LOGOUT
# ----------------------
@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")
        if username == "admin" and password == "admin123":
            session["user"] = username
            return redirect(url_for("index"))
        else:
            flash("Invalid username or password")
            return redirect(url_for("login"))
    return render_template("login.html")

@app.route("/logout")
def logout():
    session.pop("user", None)
    return redirect(url_for("login"))

# ----------------------
# INDEX / EMAIL FORM
# ----------------------
@app.route("/", methods=["GET", "POST"])
def index():
    if "user" not in session:
        return redirect(url_for("login"))

    already_analyzed = False
    previous_prediction = ""
    previous_confidence = 0
    previous_risk_message = ""

    if request.method == "POST":
        email = request.form.get("email", "").strip()
        if not email:
            flash("Email is required")
            return redirect(url_for("index"))

        # Check if email already exists in DB
        if cursor and db:
            cursor.execute("SELECT prediction, confidence FROM email_history WHERE email=%s", (email,))
            row = cursor.fetchone()
            if row:
                already_analyzed = True
                previous_prediction = row[0]
                previous_confidence = row[1]
                if previous_prediction.lower() == "safe":
                    previous_risk_message = "This email looks safe. You can use this email."
                elif previous_prediction.lower() == "medium risk":
                    previous_risk_message = "This email has some suspicious elements. Be cautious."
                else:
                    previous_risk_message = "Warning! This email is highly likely to be a phishing attempt. Don't click links in this email."

                return render_template(
                    "index.html",
                    already_analyzed=already_analyzed,
                    previous_prediction=previous_prediction,
                    previous_confidence=previous_confidence,
                    previous_risk_message=previous_risk_message
                )

        # ----------------------
        # CNN Prediction
        # ----------------------
        seq = tokenizer.texts_to_sequences([email])
        padded_seq = pad_sequences(seq, maxlen=MAX_SEQUENCE_LENGTH, padding='post')
        pred = model.predict(padded_seq)

        if pred.shape[-1] == 1:
            cnn_confidence = float(pred[0][0]) * 100
        else:
            cnn_confidence = float(pred[0][1]) * 100

        cnn_confidence = int(round(cnn_confidence))

        # ----------------------
        # Suspicious score
        # ----------------------
        suspicious_score = calculate_suspicious_score(email)

        # ----------------------
        # Final confidence and risk
        # ----------------------
        final_confidence = max(cnn_confidence, suspicious_score)

        if final_confidence >= 70:
            result = "Phishing"
            color = "red"
            risk_message = "Warning! This email is highly likely to be a phishing attempt."
        elif 30 <= final_confidence < 70:
            result = "Medium Risk"
            color = "orange"
            risk_message = "This email has some suspicious elements. Be cautious."
        else:
            result = "Safe"
            color = "green"
            risk_message = "This email looks safe."

        # ----------------------
        # Save to DB
        # ----------------------
        if cursor and db:
            cursor.execute(
                "INSERT INTO email_history (email, prediction, confidence) VALUES (%s, %s, %s)",
                (email, result, final_confidence)
            )
            db.commit()

        # ----------------------
        # Render result
        # ----------------------
        return render_template(
            "result.html",
            email=email,
            result=result,
            confidence=final_confidence,
            risk_message=risk_message,
            color=color
        )

    return render_template(
        "index.html",
        already_analyzed=already_analyzed
    )

# ----------------------
# HISTORY PAGE
# ----------------------
@app.route("/history")
def history():
    if "user" not in session:
        return redirect(url_for("login"))

    logs = []
    if cursor:
        cursor.execute("""
            SELECT email, prediction, confidence, predicted_at
            FROM email_history
            ORDER BY predicted_at DESC
        """)
        logs = cursor.fetchall()

    return render_template("history.html", logs=logs)

# ----------------------
# RUN APP
# ----------------------
if __name__ == "__main__":
    app.run(debug=True)
