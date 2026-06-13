def calculate_score(data, ai_response):
    score = 0
    severity_level = ""
    flags = []

    # Check severity from user input
    user_severity = data["severity"].lower()
    if user_severity == "severe":
        score += 40
    elif user_severity == "moderate":
        score += 25
    elif user_severity == "mild":
        score += 10

    # Check duration
    duration = data["duration"].lower()
    if any(word in duration for word in ["week", "weeks", "month", "months"]):
        score += 30
        flags.append("⚠️ Symptoms lasting this long need medical attention")
    elif any(word in duration for word in ["3 day", "4 day", "5 day", "4", "5"]):
        score += 20
    elif any(word in duration for word in ["1 day", "2 day", "today", "1", "2"]):
        score += 10

    # Check for danger keywords in symptoms
    danger_keywords = [
        "chest pain", "can't breathe", "cannot breathe", "difficulty breathing",
        "unconscious", "seizure", "stroke", "bleeding", "severe headache",
        "high fever", "vomiting blood", "heart"
    ]
    for keyword in danger_keywords:
        if keyword in data["symptoms"].lower():
            score += 40
            flags.append(f"🚨 URGENT: '{keyword}' detected — seek immediate help")
            break

    # Check AI response for severity level
    if "SEVERITY LEVEL: HIGH" in ai_response.upper():
        score += 30
    elif "SEVERITY LEVEL: MODERATE" in ai_response.upper():
        score += 20
    elif "SEVERITY LEVEL: LOW" in ai_response.upper():
        score += 5

    # Final severity level based on total score
    if score >= 70:
        severity_level = "🔴 HIGH — See a doctor immediately"
    elif score >= 40:
        severity_level = "🟡 MODERATE — See a doctor within 24-48 hours"
    else:
        severity_level = "🟢 LOW — Rest and monitor symptoms"

    return {
        "score": score,
        "severity_level": severity_level,
        "flags": flags
    }