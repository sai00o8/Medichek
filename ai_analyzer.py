from google import genai

client = genai.Client(api_key="AQ.Ab8RN6Lh_PZcH39lTbZ9h7tXOT4TcnP3mOnhGmKOKtjgbnerKw")

def analyze_symptoms(data):
    prompt = f"""
    You are a medical assistant AI. A patient has reported the following:

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
    """

    response = client.models.generate_content(
        model="gemini-2.5-flash-lite",
        contents=prompt
    )
    
    return response.text