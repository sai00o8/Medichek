from flask import Flask, render_template, request, jsonify, send_file, session, redirect, url_for
from ai_analyzer import analyze_symptoms, is_valid_symptom, get_casual_response
from scorer import calculate_score
from flask_bcrypt import Bcrypt
from report_gen import generate_pdf
from database import (
    init_db, save_session, get_history, delete_session, delete_all_sessions, 
    search_sessions, get_session_by_id, create_user, get_user_by_username
)
import os

app = Flask(__name__)
app.secret_key = "your-secret-key-change-this-later"  # needed for sessions
from datetime import timedelta
app.permanent_session_lifetime = timedelta(days=30)
bcrypt = Bcrypt(app)
init_db()

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/register", methods=["POST"])
def register():
    data = request.json
    username = data.get("username", "").strip()
    email = data.get("email", "").strip()
    password = data.get("password", "").strip()
    
    if not username or not email or not password:
        return jsonify({"error": "All fields are required"}), 400
    
    if len(password) < 6:
        return jsonify({"error": "Password must be at least 6 characters"}), 400
    
    password_hash = bcrypt.generate_password_hash(password).decode("utf-8")
    user_id = create_user(username, email, password_hash)
    
    if user_id is None:
        return jsonify({"error": "Username or email already exists"}), 400
    
    session.permanent = True
    session["user_id"] = user_id
    session["username"] = username
    
    return jsonify({"message": "Registered successfully", "username": username})

@app.route("/login", methods=["POST"])
def login():
    data = request.json
    username = data.get("username", "").strip()
    password = data.get("password", "").strip()
    
    user = get_user_by_username(username)
    
    if not user:
        return jsonify({"error": "Invalid username or password"}), 401
    
    user_id, db_username, email, password_hash = user
    
    if not bcrypt.check_password_hash(password_hash, password):
        return jsonify({"error": "Invalid username or password"}), 401
    
    session.permanent = True
    session["user_id"] = user_id
    session["username"] = db_username
    
    return jsonify({"message": "Logged in successfully", "username": db_username})

@app.route("/logout", methods=["POST"])
def logout():
    session.clear()
    return jsonify({"message": "Logged out"})

@app.route("/check-session")
def check_session():
    if "user_id" in session:
        return jsonify({"logged_in": True, "username": session["username"]})
    return jsonify({"logged_in": False})

@app.route("/analyze", methods=["POST"])
def analyze():
    if "user_id" not in session:
        return jsonify({"error": "Please log in first"}), 401
    
    data = request.json
    
    symptoms = data.get("symptoms", "").strip()
    duration = data.get("duration", "").strip()
    severity = data.get("severity", "").strip()
    
    # Validate input
    if not symptoms or not duration or not severity:
        return jsonify({"error": "Please fill in all fields"}), 400
    
    # Check if valid symptom
    if not is_valid_symptom(symptoms):
        casual = get_casual_response(symptoms)
        return jsonify({"casual": True, "message": casual})
    
    patient_data = {
        "symptoms": symptoms,
        "duration": duration,
        "severity": severity
    }
    
    # Analyze
    try:
        ai_response = analyze_symptoms(patient_data)
        score_data = calculate_score(patient_data, ai_response)
        save_session(session["user_id"], patient_data, ai_response, score_data)
        
        return jsonify({
            "casual": False,
            "ai_response": ai_response,
            "score": score_data["score"],
            "assessment": score_data["severity_level"],
            "flags": score_data["flags"]
        })
    
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/history")
def history():
    if "user_id" not in session:
        return jsonify({"error": "Please log in first"}), 401

    rows = get_history(session["user_id"])
    history_list = []
    for row in rows:
        history_list.append({
            "id": row[0],
            "date": row[1],
            "symptoms": row[2],
            "score": row[3],
            "assessment": row[4]
        })
    return jsonify(history_list)

@app.route("/history/<int:session_id>")
def full_report(session_id):
    if "user_id" not in session:
        return jsonify({"error": "Please log in first"}), 401

    row = get_session_by_id(session["user_id"], session_id)
    if not row:
        return jsonify({"error": "Session not found"}), 404
    return jsonify({
        "id": row[0],
        "date": row[1],
        "symptoms": row[2],
        "duration": row[3],
        "severity": row[4],
        "ai_response": row[5],
        "score": row[6],
        "assessment": row[7]
    })

@app.route("/history/<int:session_id>/delete", methods=["DELETE"])
def delete(session_id):
    if "user_id" not in session:
        return jsonify({"error": "Please log in first"}), 401

    success = delete_session(session["user_id"], session_id)
    if success:
        return jsonify({"message": "Deleted successfully"})
    return jsonify({"error": "Session not found"}), 404

@app.route("/history/delete-all", methods=["DELETE"])
def delete_all():
    if "user_id" not in session:
        return jsonify({"error": "Please log in first"}), 401

    delete_all_sessions(session["user_id"])
    return jsonify({"message": "All history deleted"})

@app.route("/search")
def search():
    if "user_id" not in session:
        return jsonify({"error": "Please log in first"}), 401

    keyword = request.args.get("keyword", "").strip()
    if not keyword:
        return jsonify([])
    rows = search_sessions(session["user_id"], keyword)
    results = []
    for row in rows:
        results.append({
            "id": row[0],
            "date": row[1],
            "symptoms": row[2],
            "score": row[3],
            "assessment": row[4]
        })
    return jsonify(results)

@app.route("/export-pdf", methods=["POST"])
def export_pdf():
    if "user_id" not in session:
        return jsonify({"error": "Please log in first"}), 401

    data = request.json
    patient_data = {
        "symptoms": data["symptoms"],
        "duration": data["duration"],
        "severity": data["severity"]
    }
    score_data = {
        "score": data["score"],
        "severity_level": data["assessment"],
        "flags": data.get("flags", [])
    }
    try:
        pdf_file = generate_pdf(patient_data, data["ai_response"], score_data)
        return send_file(pdf_file, as_attachment=True)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    app.run(debug=True)