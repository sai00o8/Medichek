from flask import Flask, render_template, request, jsonify, send_file
from ai_analyzer import analyze_symptoms, is_valid_symptom, get_casual_response
from scorer import calculate_score
from database import init_db, save_session, get_history, delete_session, delete_all_sessions, search_sessions, get_session_by_id
from report_gen import generate_pdf
import os

app = Flask(__name__)

# Initialize database on startup
init_db()

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/analyze", methods=["POST"])
def analyze():
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
        save_session(patient_data, ai_response, score_data)
        
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
    rows = get_history()
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
    row = get_session_by_id(session_id)
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
    success = delete_session(session_id)
    if success:
        return jsonify({"message": "Deleted successfully"})
    return jsonify({"error": "Session not found"}), 404

@app.route("/history/delete-all", methods=["DELETE"])
def delete_all():
    delete_all_sessions()
    return jsonify({"message": "All history deleted"})

@app.route("/search")
def search():
    keyword = request.args.get("keyword", "").strip()
    if not keyword:
        return jsonify([])
    rows = search_sessions(keyword)
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