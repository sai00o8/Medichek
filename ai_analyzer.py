from groq import Groq
import time
import httpx

client = Groq(api_key="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")

def is_valid_symptom(text):
    # First check locally — no API call needed
    casual_words = [
        "hi", "hello", "hey", "how are you", "what is this",
        "testing", "test", "who are you", "good morning", "good evening",
        "good night", "bye", "ok", "okay", "thanks", "thank you",
        "what", "why", "when", "where", "how", "sup", "yo"
    ]
    
    text_lower = text.lower().strip()
    
    # If it matches casual words, no API call needed
    if text_lower in casual_words:
        return False
    
    # If its too short to be a symptom
    if len(text_lower) < 4:
        return False
    
    # If it looks like a real symptom skip API call entirely
    symptom_hints = [
        "pain", "ache", "fever", "cough", "cold", "headache", "nausea",
        "vomit", "dizzy", "tired", "fatigue", "sore", "throat", "stomach",
        "chest", "back", "leg", "arm", "eye", "ear", "nose", "skin",
        "rash", "itch", "swollen", "bleeding", "breath", "heart"
    ]
    
    if any(hint in text_lower for hint in symptom_hints):
        return True
    
    # Only call API if we genuinely can't tell
    response = client.chat.completions.create(
        model="openai/gpt-oss-120b",
        messages=[{"role": "user", "content": f"""
        A user typed this into a medical symptom checker: "{text}"
        Is this a real medical symptom or health complaint?
        Reply with only ONE word: YES or NO
        """}]
    )
    answer = response.choices[0].message.content.strip().upper()
    return "YES" in answer

def get_casual_response(text):
    response = client.chat.completions.create(
        model="openai/gpt-oss-120b",
        messages=[{"role": "user", "content": f"""
        You are MediCheck, a friendly medical assistant chatbot.
        The user said: "{text}"
        This is not a medical symptom. Respond warmly, introduce yourself 
        briefly and ask if they have any symptoms you can help with.
        Keep it to 2-3 sentences maximum.
        """}]
    )
    return response.choices[0].message.content.strip()

def analyze_symptoms(data):
    response = client.chat.completions.create(
        model="openai/gpt-oss-120b",
        messages=[{"role": "user", "content": f"""
        You are a medical assistant AI. A patient has reported:

        Symptoms: {data['symptoms']}
        Duration: {data['duration']}
        Severity: {data['severity']}

        Respond in this exact format:
        POSSIBLE CONDITIONS:
        1. [condition name] - [% match] - [one line explanation]
        2. [condition name] - [% match] - [one line explanation]
        3. [condition name] - [% match] - [one line explanation]

        SEVERITY LEVEL: [LOW / MODERATE / HIGH]

        RECOMMENDATION: [What should the patient do]

        DISCLAIMER: This is not a substitute for professional medical advice.
        """}]
    )
    return response.choices[0].message.content.strip()