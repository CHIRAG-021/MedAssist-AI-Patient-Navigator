"""
================================================================================
  MedAssist Patient Care Navigator — Flask Backend
  Powered by IBM Watsonx.ai with Granite Models
================================================================================
"""

import os
import re
import json
from datetime import datetime, date
from flask import Flask, request, jsonify, render_template, session
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# ============================================================
#  AGENT INSTRUCTIONS (Edit this section to customize behavior)
#  Full instructions are also in AGENT_INSTRUCTIONS.txt
# ============================================================
AGENT_INSTRUCTIONS = """
You are MedAssist, a compassionate AI health companion for Indian patients.
Your role is strictly EDUCATIONAL — you do NOT diagnose or prescribe.

CORE BEHAVIOR:
- Respond with empathy, warmth, and clarity.
- Detect Hindi / Hinglish input and respond in the same language.
- Structure responses using the format below.
- Always ground advice in WHO, CDC, and ICMR guidelines.

RESPONSE FORMAT (follow this exactly for symptom queries):
1. Empathy opener (1 sentence)
2. Clarifying questions (if this is the first mention of a symptom — ask age, duration, existing conditions)
3. Probable Educational Causes (list 2-4, clearly labeled as educational, NOT diagnosis)
4. URGENCY LEVEL: [ROUTINE / MODERATE / URGENT] — explain why
5. Recommended Specialist type
6. Home Remedies (ONLY for ROUTINE — use Indian ingredients: ginger, tulsi, haldi doodh, ORS, steam inhalation)
7. 2-3 Preventive Tips (relevant to symptom and age; use Indian food references)
8. Warning Signs to NOT ignore
9. Source: Based on WHO/CDC/ICMR guidelines

URGENCY RULES:
- ROUTINE: cold, mild fever, indigestion, minor aches
- MODERATE: fever >3 days, persistent pain, uncontrolled BP/sugar
- URGENT: chest pain, difficulty breathing, stroke signs, loss of consciousness → say "SEEK EMERGENCY CARE — Call 108"

INDIAN HEALTH CONTEXT:
- Use Indian food refs: dal, roti, sabzi, khichdi, curd, coconut water, amla, tulsi, neem, jeera, ajwain, methi
- Common conditions: diabetes, hypertension, typhoid, dengue, malaria, anaemia, TB, PCOS
- Emergency number: 108 (India ambulance)
- Mental health: NIMHANS 080-46110007, iCall 9152987821

MEDICATION TRACKER HELP:
When asked about medication adherence or reminders, provide:
- General adherence tips (take with food/water as prescribed, set alarms, pill organizer)
- NEVER recommend specific drugs or dosages

SAFETY RULES (ABSOLUTE — NEVER BREAK):
1. NEVER diagnose any medical condition.
2. NEVER recommend specific medications, brands, or dosages.
3. ALWAYS end every health response with: "⚕️ Please consult a licensed doctor for proper diagnosis and treatment."
4. For URGENT symptoms: prepend "🚨 SEEK EMERGENCY CARE IMMEDIATELY — Call 108"
5. For mental health mentions: immediately provide NIMHANS helpline 080-46110007

BMI INTERPRETATION GUIDE (for when you receive BMI data):
- Below 18.5: Underweight — suggest nutritional assessment
- 18.5-22.9: Normal (healthy range for Indians per ICMR)
- 23-24.9: Overweight (Indian threshold is lower than Western standard)
- 25-29.9: Obese Class I
- 30+: Obese Class II — recommend physician consultation

PREVENTIVE TIPS BY CONDITION:
Diabetes: reduce refined sugar/white rice, walk 30 min/day, monitor HbA1c, eat methi seeds
Hypertension: reduce salt/achaar/papad, meditate, target BP <130/80, eat banana and coconut water
General: sleep 7-8 hrs, drink 8-10 glasses water, annual health checkup, stay vaccinated
"""

# ============================================================
#  APPLICATION SETUP
# ============================================================
app = Flask(__name__)
app.secret_key = os.getenv("FLASK_SECRET_KEY", "medassist-dev-secret-change-in-production")

# ============================================================
#  WATSONX.AI CONFIGURATION
# ============================================================
WATSONX_API_KEY   = os.getenv("WATSONX_API_KEY")
WATSONX_PROJECT_ID = os.getenv("WATSONX_PROJECT_ID")
WATSONX_URL       = os.getenv("WATSONX_URL", "https://us-south.ml.cloud.ibm.com")
MODEL_ID          = os.getenv("WATSONX_MODEL_ID", "ibm/granite-3-3-8b-instruct")

# Generation parameters (override via .env)
GENERATION_PARAMS = {
    "max_new_tokens":    int(os.getenv("MAX_NEW_TOKENS", 1024)),
    "min_new_tokens":    int(os.getenv("MIN_NEW_TOKENS", 50)),
    "temperature":       float(os.getenv("TEMPERATURE", 0.3)),
    "top_p":             float(os.getenv("TOP_P", 0.9)),
    "top_k":             int(os.getenv("TOP_K", 50)),
    "repetition_penalty": float(os.getenv("REPETITION_PENALTY", 1.1)),
}

# ============================================================
#  WATSONX CLIENT INITIALISATION
# ============================================================
watsonx_client = None

def init_watsonx():
    """Initialise IBM Watsonx.ai client. Returns client or None on failure."""
    global watsonx_client
    if not WATSONX_API_KEY or not WATSONX_PROJECT_ID:
        print("⚠️  WARNING: WATSONX_API_KEY or WATSONX_PROJECT_ID not set in .env")
        return None
    try:
        from ibm_watsonx_ai import Credentials
        from ibm_watsonx_ai.foundation_models import ModelInference
        credentials = Credentials(url=WATSONX_URL, api_key=WATSONX_API_KEY)
        watsonx_client = ModelInference(
            model_id=MODEL_ID,
            credentials=credentials,
            project_id=WATSONX_PROJECT_ID,
            params=GENERATION_PARAMS,
        )
        print(f"✅ Watsonx.ai client initialised — model: {MODEL_ID}")
        return watsonx_client
    except Exception as e:
        print(f"❌ Failed to initialise Watsonx.ai: {e}")
        return None

# Initialise on startup
init_watsonx()

# ============================================================
#  LANGUAGE DETECTION
# ============================================================
def detect_language(text: str) -> str:
    """Detect if input is Hindi/Hinglish or English."""
    hindi_pattern = re.compile(
        r'[\u0900-\u097F]'  # Devanagari Unicode block
    )
    hindi_words = [
        "mujhe", "mere", "mera", "kya", "hai", "ho", "hoon", "nahi", "bahut",
        "dard", "bukhar", "sar", "pet", "sir", "thoda", "zyada", "acha",
        "theek", "taklif", "bimari", "doctor", "davai", "khana", "peena"
    ]
    text_lower = text.lower()
    if hindi_pattern.search(text):
        return "hindi"
    if any(word in text_lower for word in hindi_words):
        return "hinglish"
    return "english"

# ============================================================
#  URGENCY DETECTION (pre-LLM safety check)
# ============================================================
URGENT_KEYWORDS = [
    "chest pain", "heart attack", "difficulty breathing", "can't breathe",
    "stroke", "unconscious", "not breathing", "severe bleeding", "poisoning",
    "overdose", "anaphylaxis", "seizure", "convulsion", "paralysis",
    "severe headache suddenly", "vision loss suddenly", "collapsed",
    "saans nahi", "chati mein dard", "behosh", "tez dard"
]

MENTAL_HEALTH_KEYWORDS = [
    "suicide", "self harm", "self-harm", "want to die", "kill myself",
    "depression", "anxiety", "panic attack", "mental health",
    "khatam karna", "jeena nahi", "udas", "ghabrahat"
]

def check_urgent_keywords(text: str) -> dict:
    """Pre-screen input for urgent/mental health keywords before sending to LLM."""
    text_lower = text.lower()
    is_urgent = any(kw in text_lower for kw in URGENT_KEYWORDS)
    is_mental = any(kw in text_lower for kw in MENTAL_HEALTH_KEYWORDS)
    return {"is_urgent": is_urgent, "is_mental_health": is_mental}

# ============================================================
#  LLM QUERY
# ============================================================
def query_watsonx(user_message: str, conversation_history: list, language: str) -> str:
    """Build prompt and query Watsonx.ai Granite model."""
    if not watsonx_client:
        return get_fallback_response(user_message, language)

    # Build conversation context (last 6 turns to stay within token limits)
    history_text = ""
    for turn in conversation_history[-6:]:
        role = "User" if turn["role"] == "user" else "MedAssist"
        history_text += f"{role}: {turn['content']}\n"

    lang_instruction = ""
    if language == "hindi":
        lang_instruction = "IMPORTANT: The user is writing in Hindi. Please respond entirely in Hindi (Devanagari script)."
    elif language == "hinglish":
        lang_instruction = "IMPORTANT: The user is writing in Hinglish (Hindi-English mix). Please respond in Hinglish."

    prompt = f"""<|system|>
{AGENT_INSTRUCTIONS}
{lang_instruction}
<|user|>
Previous conversation:
{history_text}
Current message: {user_message}
<|assistant|>"""

    try:
        response = watsonx_client.generate_text(prompt=prompt)
        return response.strip() if response else get_fallback_response(user_message, language)
    except Exception as e:
        print(f"❌ Watsonx query error: {e}")
        return get_fallback_response(user_message, language)

def get_fallback_response(message: str, language: str) -> str:
    """Fallback response when Watsonx.ai is unavailable."""
    if language == "hindi":
        return (
            "क्षमा करें, अभी AI सेवा उपलब्ध नहीं है। कृपया अपने IBM Watsonx.ai "
            "credentials को .env फ़ाइल में सेट करें और पुनः प्रयास करें।\n\n"
            "⚕️ किसी भी स्वास्थ्य समस्या के लिए, कृपया एक लाइसेंस प्राप्त डॉक्टर से परामर्श करें।"
        )
    return (
        "⚠️ AI service is currently unavailable. Please ensure your IBM Watsonx.ai credentials "
        "are correctly set in the .env file (WATSONX_API_KEY and WATSONX_PROJECT_ID).\n\n"
        "In the meantime, please consult a licensed healthcare professional for any medical concerns.\n\n"
        "⚕️ Please consult a licensed doctor for proper diagnosis and treatment."
    )

# ============================================================
#  BMI CALCULATION
# ============================================================
def calculate_bmi(weight_kg: float, height_cm: float) -> dict:
    """Calculate BMI and return category using Indian-specific thresholds (ICMR)."""
    if height_cm <= 0 or weight_kg <= 0:
        return {"bmi": 0, "category": "Invalid", "color": "secondary", "advice": ""}

    height_m = height_cm / 100
    bmi = round(weight_kg / (height_m ** 2), 1)

    # ICMR recommends lower thresholds for South Asians
    if bmi < 18.5:
        category, color, advice = "Underweight", "info", "Consider a nutritional assessment. Eat calorie-dense foods like nuts, ghee in moderation, and dals."
    elif bmi < 23:
        category, color, advice = "Normal (Healthy)", "success", "Great! Maintain your healthy weight with balanced diet and regular exercise."
    elif bmi < 25:
        category, color, advice = "Overweight", "warning", "Slightly above Indian healthy range. Reduce refined carbs and increase physical activity."
    elif bmi < 30:
        category, color, advice = "Obese Class I", "danger", "Consider consulting a physician and dietitian. Focus on portion control and daily walks."
    else:
        category, color, advice = "Obese Class II", "danger", "Please consult a physician promptly. Structured weight management is recommended."

    return {"bmi": bmi, "category": category, "color": color, "advice": advice}

# ============================================================
#  ADHERENCE CALCULATION
# ============================================================
def calculate_adherence(medications: list) -> float:
    """Calculate overall medication adherence percentage."""
    if not medications:
        return 0.0
    total_doses = sum(m.get("total_doses", 0) for m in medications)
    taken_doses = sum(m.get("taken_doses", 0) for m in medications)
    if total_doses == 0:
        return 0.0
    return round((taken_doses / total_doses) * 100, 1)

# ============================================================
#  ROUTES
# ============================================================
@app.route("/")
def index():
    """Serve the main application page."""
    if "chat_history" not in session:
        session["chat_history"] = []
    if "family_profiles" not in session:
        session["family_profiles"] = []
    if "medications" not in session:
        session["medications"] = []
    if "appointments" not in session:
        session["appointments"] = []
    return render_template("index.html")

@app.route("/api/chat", methods=["POST"])
def chat():
    """Handle chat messages — core symptom triage endpoint."""
    data = request.get_json()
    if not data or "message" not in data:
        return jsonify({"error": "Message is required"}), 400

    user_message = data.get("message", "").strip()
    if not user_message:
        return jsonify({"error": "Empty message"}), 400

    # Language detection
    language = detect_language(user_message)

    # Pre-screen for urgent / mental health keywords
    keyword_check = check_urgent_keywords(user_message)

    # Get or init chat history from session
    if "chat_history" not in session:
        session["chat_history"] = []

    # Query LLM
    ai_response = query_watsonx(user_message, session["chat_history"], language)

    # Append urgent alerts if keyword-triggered (belt-and-suspenders safety)
    if keyword_check["is_urgent"] and "108" not in ai_response:
        ai_response = "🚨 SEEK EMERGENCY CARE IMMEDIATELY — Call 108\n\n" + ai_response
    if keyword_check["is_mental_health"] and "080-46110007" not in ai_response:
        ai_response += "\n\n💛 If you are struggling mentally, please reach out:\n• NIMHANS Helpline: 080-46110007\n• iCall: 9152987821"

    # Save to session history
    session["chat_history"].append({"role": "user",      "content": user_message})
    session["chat_history"].append({"role": "assistant", "content": ai_response})
    session.modified = True

    # Detect urgency level for badge color
    urgency = "ROUTINE"
    if "URGENT" in ai_response.upper() or keyword_check["is_urgent"]:
        urgency = "URGENT"
    elif "MODERATE" in ai_response.upper():
        urgency = "MODERATE"

    return jsonify({
        "response":  ai_response,
        "language":  language,
        "urgency":   urgency,
        "timestamp": datetime.now().strftime("%I:%M %p"),
        "is_urgent": keyword_check["is_urgent"],
        "is_mental": keyword_check["is_mental_health"],
    })

@app.route("/api/chat/clear", methods=["POST"])
def clear_chat():
    """Clear the chat history for the current session."""
    session["chat_history"] = []
    session.modified = True
    return jsonify({"status": "cleared"})

@app.route("/api/bmi", methods=["POST"])
def bmi():
    """Calculate BMI and return category with advice."""
    data = request.get_json()
    try:
        weight = float(data.get("weight", 0))
        height = float(data.get("height", 0))
        result = calculate_bmi(weight, height)

        # Optional: save profile to session
        profile = {
            "name":       data.get("name", ""),
            "age":        data.get("age", ""),
            "gender":     data.get("gender", ""),
            "height":     height,
            "weight":     weight,
            "conditions": data.get("conditions", ""),
            "bmi":        result["bmi"],
            "bmi_category": result["category"],
        }
        if "family_profiles" not in session:
            session["family_profiles"] = []

        # Update existing or add new profile
        profiles = session["family_profiles"]
        existing = next((p for p in profiles if p.get("name") == profile["name"]), None)
        if existing:
            existing.update(profile)
        else:
            profiles.append(profile)
        session.modified = True

        return jsonify({**result, "profile": profile})
    except (ValueError, TypeError) as e:
        return jsonify({"error": f"Invalid data: {e}"}), 400

@app.route("/api/medications", methods=["GET", "POST"])
def medications():
    """Get or add medications for the tracker."""
    if "medications" not in session:
        session["medications"] = []

    if request.method == "GET":
        meds = session["medications"]
        adherence = calculate_adherence(meds)
        return jsonify({"medications": meds, "adherence": adherence})

    data = request.get_json()
    med = {
        "id":          len(session["medications"]) + 1,
        "name":        data.get("name", ""),
        "dosage":      data.get("dosage", ""),
        "frequency":   data.get("frequency", ""),
        "time":        data.get("time", ""),
        "total_doses": int(data.get("total_doses", 30)),
        "taken_doses": int(data.get("taken_doses", 0)),
        "notes":       data.get("notes", ""),
        "added_on":    date.today().isoformat(),
    }
    session["medications"].append(med)
    session.modified = True
    adherence = calculate_adherence(session["medications"])
    return jsonify({"medication": med, "adherence": adherence, "status": "added"})

@app.route("/api/medications/<int:med_id>/take", methods=["POST"])
def take_medication(med_id):
    """Mark a dose as taken for a medication."""
    if "medications" not in session:
        return jsonify({"error": "No medications found"}), 404
    for med in session["medications"]:
        if med["id"] == med_id:
            med["taken_doses"] = min(med["taken_doses"] + 1, med["total_doses"])
            session.modified = True
            adherence = calculate_adherence(session["medications"])
            return jsonify({"medication": med, "adherence": adherence})
    return jsonify({"error": "Medication not found"}), 404

@app.route("/api/medications/<int:med_id>", methods=["DELETE"])
def delete_medication(med_id):
    """Delete a medication from the tracker."""
    if "medications" not in session:
        return jsonify({"error": "No medications found"}), 404
    session["medications"] = [m for m in session["medications"] if m["id"] != med_id]
    session.modified = True
    adherence = calculate_adherence(session["medications"])
    return jsonify({"status": "deleted", "adherence": adherence})

@app.route("/api/appointments", methods=["GET", "POST"])
def appointments():
    """Get or add appointment reminders."""
    if "appointments" not in session:
        session["appointments"] = []

    if request.method == "GET":
        appts = sorted(session["appointments"], key=lambda x: x.get("date", ""))
        today = date.today().isoformat()
        for appt in appts:
            appt["is_upcoming"] = appt.get("date", "") >= today
        return jsonify({"appointments": appts})

    data = request.get_json()
    appt = {
        "id":       len(session["appointments"]) + 1,
        "doctor":   data.get("doctor", ""),
        "type":     data.get("type", ""),
        "date":     data.get("date", ""),
        "time":     data.get("time", ""),
        "location": data.get("location", ""),
        "notes":    data.get("notes", ""),
    }
    session["appointments"].append(appt)
    session.modified = True
    return jsonify({"appointment": appt, "status": "added"})

@app.route("/api/appointments/<int:appt_id>", methods=["DELETE"])
def delete_appointment(appt_id):
    """Delete an appointment."""
    if "appointments" not in session:
        return jsonify({"error": "No appointments found"}), 404
    session["appointments"] = [a for a in session["appointments"] if a["id"] != appt_id]
    session.modified = True
    return jsonify({"status": "deleted"})

@app.route("/api/family", methods=["GET"])
def family_profiles():
    """Return all family health profiles."""
    profiles = session.get("family_profiles", [])
    return jsonify({"profiles": profiles})

@app.route("/api/tips", methods=["GET"])
def health_tips():
    """Return preventive health tips by category."""
    tips = {
        "diabetes": [
            {"tip": "Reduce refined sugar & white rice; choose millets (jowar, bajra) or brown rice.", "icon": "🌾"},
            {"tip": "Walk 30 minutes daily. Yoga (Surya Namaskar) and pranayama help regulate blood sugar.", "icon": "🧘"},
            {"tip": "Monitor HbA1c every 3 months; target below 7.0%. Keep a log of readings.", "icon": "📊"},
            {"tip": "Soak 1 tsp methi (fenugreek) seeds overnight; drink the water on an empty stomach.", "icon": "🌿"},
            {"tip": "Get regular eye and kidney checkups — diabetes can silently damage both organs.", "icon": "👁️"},
        ],
        "hypertension": [
            {"tip": "Reduce sodium — avoid achaar (pickle), papad, processed & packaged foods.", "icon": "🧂"},
            {"tip": "Practice deep breathing (Anulom-Vilom) and meditation for 10-15 minutes daily.", "icon": "💨"},
            {"tip": "Monitor BP at home; target <130/80 mmHg. Log readings with dates.", "icon": "💓"},
            {"tip": "Eat potassium-rich foods: banana, coconut water, palak (spinach), sweet potato.", "icon": "🍌"},
            {"tip": "Limit alcohol and quit smoking completely — both significantly raise BP.", "icon": "🚭"},
        ],
        "general": [
            {"tip": "Sleep 7-8 hours per night. Maintain a consistent sleep-wake schedule.", "icon": "😴"},
            {"tip": "Drink 8-10 glasses of water daily; increase during summer and illness.", "icon": "💧"},
            {"tip": "Eat a rainbow diet — include colourful fruits and vegetables every day.", "icon": "🥦"},
            {"tip": "Annual health checkup: CBC, lipid profile, blood sugar, thyroid, Vit D & B12.", "icon": "🏥"},
            {"tip": "Stay updated on vaccinations — flu shot annually, COVID booster as recommended.", "icon": "💉"},
            {"tip": "Amla (Indian gooseberry) daily boosts immunity and provides natural Vitamin C.", "icon": "🍋"},
        ],
    }
    return jsonify(tips)

@app.route("/api/health")
def health_check():
    """Simple health check endpoint."""
    return jsonify({
        "status":  "ok",
        "model":   MODEL_ID,
        "watsonx": "connected" if watsonx_client else "not_configured",
        "version": os.getenv("APP_VERSION", "1.0.0"),
    })

# ============================================================
#  ENTRY POINT
# ============================================================
if __name__ == "__main__":
    port = int(os.getenv("FLASK_PORT", 5000))
    debug = os.getenv("FLASK_DEBUG", "True").lower() == "true"
    print(f"🏥 MedAssist starting on http://localhost:{port}")
    print(f"📋 Model: {MODEL_ID}")
    print(f"🔗 Watsonx URL: {WATSONX_URL}")
    app.run(host="0.0.0.0", port=port, debug=debug)
