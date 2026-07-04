# 🏥 MedAssist — Patient Care Navigator

![Python](https://img.shields.io/badge/Python-3.9%2B-blue?logo=python)
![Flask](https://img.shields.io/badge/Flask-3.0-black?logo=flask)
![IBM Watsonx.ai](https://img.shields.io/badge/IBM-Watsonx.ai-0f62fe?logo=ibm)
![Granite](https://img.shields.io/badge/Model-Granite--3.3--8B-purple)
![License](https://img.shields.io/badge/License-MIT-green)

> An AI-powered healthcare companion built with **Python Flask** and **IBM Watsonx.ai (Granite models)**.  
> Designed for Indian patients — multilingual symptom triage, medication tracking, appointment reminders, and preventive health tips.

---

## ✨ Features

| Feature | Description |
|---|---|
| 💬 **Symptom Chat** | Natural language triage in English, Hindi & Hinglish |
| 🚨 **Urgency Levels** | Colour-coded responses: `ROUTINE` / `MODERATE` / `URGENT` |
| 💊 **Medication Tracker** | Adherence dashboard with per-dose tracking |
| 📅 **Appointment Manager** | Upcoming & past appointment reminders |
| 🧍 **BMI Calculator** | Uses ICMR South Asian thresholds (lower than Western standard) |
| 👨‍👩‍👧 **Family Profiles** | Multi-member health profile support |
| 🌿 **Preventive Tips** | Diabetes, Hypertension, and General Wellness categories |
| 🌐 **WHO/CDC Grounding** | Every response sourced from WHO, CDC & ICMR guidelines |
| 🌙 **Dark Mode** | Toggle between light and dark themes |
| 🇮🇳 **Hindi / Hinglish** | Auto-detects script/language and responds in kind |

---

## 📁 Project Structure

```
medassist/
├── app.py                   # Flask backend — all routes & Watsonx.ai integration
├── templates/
│   └── index.html           # Responsive single-page frontend (Bootstrap 5)
├── static/
│   ├── style.css            # Custom CSS — light/dark theme, healthcare UI
│   └── script.js            # Frontend logic — chat, medications, appointments
├── .env.example             # Template for environment variables (safe to commit)
├── .gitignore               # Ignores .env, venv/, __pycache__/, etc.
├── requirements.txt         # Python dependencies
├── AGENT_INSTRUCTIONS.txt   # Customizable agent behavior & rules
└── README.md                # This file
```

---

## 🚀 Quick Start

### Prerequisites

- Python **3.9+**
- An [IBM Cloud](https://cloud.ibm.com) account
- IBM Watsonx.ai project with Granite model access

---

### Step 1 — Clone the repository

```bash
git clone https://github.com/<your-username>/medassist.git
cd medassist
```

### Step 2 — Create a virtual environment

```bash
python3 -m venv venv

# Linux / macOS
source venv/bin/activate

# Windows
venv\Scripts\activate
```

### Step 3 — Install dependencies

```bash
pip install -r requirements.txt
```

### Step 4 — Configure credentials

1. Go to [IBM Cloud IAM](https://cloud.ibm.com/iam/apikeys) → create an API key
2. Open [IBM Watsonx.ai](https://dataplatform.cloud.ibm.com/) → create a project → copy the Project ID
3. Copy the environment template and fill in your values:

```bash
cp .env.example .env
```

```dotenv
WATSONX_API_KEY=your_ibm_cloud_api_key
WATSONX_PROJECT_ID=your_watsonx_project_id
WATSONX_URL=https://us-south.ml.cloud.ibm.com
WATSONX_MODEL_ID=ibm/granite-3-3-8b-instruct
FLASK_SECRET_KEY=generate-a-long-random-string-here
```

> **Tip:** Generate a secure Flask secret key instantly:
> ```bash
> python3 -c "import secrets; print(secrets.token_hex(32))"
> ```

### Step 5 — Run the app

```bash
python app.py
```

Open **http://localhost:5000** in your browser.

---

## 🌐 Environment Variables

| Variable | Required | Default | Description |
|---|---|---|---|
| `WATSONX_API_KEY` | ✅ | — | IBM Cloud API key |
| `WATSONX_PROJECT_ID` | ✅ | — | Watsonx.ai project ID |
| `WATSONX_URL` | ✅ | `us-south.ml.cloud.ibm.com` | Watsonx.ai regional endpoint |
| `WATSONX_MODEL_ID` | Optional | `granite-3-3-8b-instruct` | Granite model to use |
| `FLASK_SECRET_KEY` | ✅ | — | Flask session secret (min 32 chars) |
| `FLASK_DEBUG` | Optional | `True` | Set `False` in production |
| `FLASK_PORT` | Optional | `5000` | Port to listen on |
| `MAX_NEW_TOKENS` | Optional | `1024` | Max tokens per AI response |
| `TEMPERATURE` | Optional | `0.3` | Model temperature (0 = focused, 1 = creative) |

---

## 🔄 Switching the Granite Model

Edit `WATSONX_MODEL_ID` in your `.env` file — no code changes needed:

```dotenv
# Latest (default)
WATSONX_MODEL_ID=ibm/granite-3-3-8b-instruct

# Other available Granite models
WATSONX_MODEL_ID=ibm/granite-3-2-8b-instruct
WATSONX_MODEL_ID=ibm/granite-3-1-8b-instruct
WATSONX_MODEL_ID=ibm/granite-13b-chat-v2
```

---

## ⚙️ Customizing Agent Behavior

The AI prompt lives in two places:

- **`AGENT_INSTRUCTIONS.txt`** — human-readable documentation of the rules
- **`app.py` → `AGENT_INSTRUCTIONS` variable (~line 22)** — the actual system prompt injected into Granite

Edit the `AGENT_INSTRUCTIONS` string in `app.py` to change tone, urgency rules, supported conditions, language behavior, or home remedy references.

---

## 🔒 Security Notes

- **Never** commit `.env` — it is already excluded by `.gitignore`
- Rotate your IBM Cloud API key periodically
- Set `FLASK_DEBUG=False` and `FLASK_ENV=production` in production
- Use [IBM Secrets Manager](https://cloud.ibm.com/catalog/services/secrets-manager) for production credential storage

---

## ⚕️ Medical Disclaimer

MedAssist is an **educational tool only**.  
It does **NOT** diagnose, prescribe, or replace professional medical advice.  
Always consult a licensed physician for any health concerns.

> 🇮🇳 **Emergency in India? Call 108** (National Ambulance Service)

---

## 📜 License

MIT License — see [LICENSE](LICENSE) for details.

---

*Powered by IBM Watsonx.ai · Granite Models · Built with Flask & Bootstrap 5*
