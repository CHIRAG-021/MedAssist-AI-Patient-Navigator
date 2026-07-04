# 🏥 MedAssist Patient Care Navigator

> An AI-powered healthcare companion built with **Python Flask** + **IBM Watsonx.ai (Granite models)**  
> Designed for Indian patients with multilingual support, symptom triage, medication tracking, and preventive health tips.

---

## ✨ Features

| Feature | Description |
|---|---|
| 💬 **Symptom Chat** | Natural language triage in English, Hindi & Hinglish |
| 🚨 **Urgency Levels** | Colour-coded: ROUTINE / MODERATE / URGENT |
| 💊 **Medication Tracker** | Adherence dashboard with dose tracking |
| 📅 **Appointment Manager** | Upcoming & past appointment reminders |
| 🧍 **BMI Calculator** | ICMR South Asian thresholds |
| 👨‍👩‍👧 **Family Profiles** | Multi-member health profile support |
| 🌿 **Preventive Tips** | Diabetes, Hypertension, General Wellness |
| 🌐 **WHO/CDC Grounding** | Every response sourced from WHO & CDC guidelines |
| 🌙 **Dark Mode** | Toggle between light and dark themes |
| 🇮🇳 **Hindi Support** | Auto-detects Hindi/Hinglish and responds accordingly |

---

## 📁 Project Structure

```
medassist/
├── app.py                   # Flask backend — all routes & Watsonx.ai integration
├── templates/
│   └── index.html           # Complete responsive frontend (Bootstrap 5)
├── static/
│   ├── style.css            # Custom CSS — light/dark theme, healthcare UI
│   └── script.js            # Frontend logic — chat, medications, appointments
├── .env.example             # Template for environment variables
├── .env                     # Your actual credentials (DO NOT COMMIT)
├── requirements.txt         # Python dependencies
├── AGENT_INSTRUCTIONS.txt   # Customizable agent behavior & rules
└── README.md                # This file
```

---

## 🚀 Local Setup — Step by Step

### Prerequisites

- Python 3.9 or higher
- An IBM Cloud account
- IBM Watsonx.ai project with Granite model access

---

### Step 1 — Clone / Download the project

```bash
# If using git
git clone <your-repo-url>
cd medassist

# Or simply navigate to the medassist/ directory
```

### Step 2 — Create a Python virtual environment

```bash
python3 -m venv venv

# Activate (Linux/macOS)
source venv/bin/activate

# Activate (Windows)
venv\Scripts\activate
```

### Step 3 — Install dependencies

```bash
pip install -r requirements.txt
```

### Step 4 — Configure IBM Watsonx.ai credentials

1. Go to [IBM Cloud IAM](https://cloud.ibm.com/iam/apikeys) → create an API key  
2. Open [IBM Watsonx.ai](https://dataplatform.cloud.ibm.com/) → create a project → copy the Project ID  
3. Copy the environment template:

```bash
cp .env.example .env
```

4. Edit `.env` and fill in your credentials:

```bash
# Open with any text editor
nano .env   # or: code .env, vim .env, notepad .env
```

Fill in these values:
```dotenv
WATSONX_API_KEY=your_actual_ibm_cloud_api_key
WATSONX_PROJECT_ID=your_actual_watsonx_project_id
WATSONX_URL=https://us-south.ml.cloud.ibm.com
WATSONX_MODEL_ID=ibm/granite-3-3-8b-instruct
FLASK_SECRET_KEY=generate-a-long-random-string-here
```

> **Tip:** Generate a secure Flask secret key:
> ```bash
> python3 -c "import secrets; print(secrets.token_hex(32))"
> ```

### Step 5 — Run the application

```bash
python app.py
```

Open your browser at: **http://localhost:5000**

---

## 🔄 How to Change the Granite Model

Edit your `.env` file and change `WATSONX_MODEL_ID`:

```dotenv
# Latest recommended (default)
WATSONX_MODEL_ID=ibm/granite-3-3-8b-instruct

# Other available Granite models
WATSONX_MODEL_ID=ibm/granite-3-2-8b-instruct
WATSONX_MODEL_ID=ibm/granite-3-1-8b-instruct
WATSONX_MODEL_ID=ibm/granite-3-0-8b-instruct
WATSONX_MODEL_ID=ibm/granite-13b-chat-v2
```

No code changes needed — the model is loaded from `.env` on startup.

You can also change it directly in `app.py` line:
```python
MODEL_ID = os.getenv("WATSONX_MODEL_ID", "ibm/granite-3-3-8b-instruct")
```

---

## ⚙️ Customizing Agent Behavior

All agent rules are in two places:

### 1. `AGENT_INSTRUCTIONS.txt` — Human-readable documentation
Edit this file to document your customization decisions.

### 2. `app.py` → `AGENT_INSTRUCTIONS` variable (line ~28)
This is the actual prompt injected into the Granite model. Edit this to:
- Change the agent's tone or personality
- Add/modify urgency rules
- Add new Indian health conditions
- Change language behavior
- Adjust home remedy references

---

## ☁️ Deploy to IBM Cloud Code Engine

### Prerequisites
- IBM Cloud CLI installed: `curl -fsSL https://clis.cloud.ibm.com/install/linux | sh`
- Code Engine plugin: `ibmcloud plugin install code-engine`

### Step 1 — Login to IBM Cloud

```bash
ibmcloud login --apikey YOUR_IBM_CLOUD_API_KEY -r us-south
ibmcloud target -g Default
```

### Step 2 — Create a Code Engine project

```bash
ibmcloud ce project create --name medassist-project
ibmcloud ce project select --name medassist-project
```

### Step 3 — Create a container image (Option A: using Docker)

```bash
# Add this Dockerfile to your medassist/ directory:
cat > Dockerfile <<'EOF'
FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
EXPOSE 8080
CMD ["gunicorn", "--bind", "0.0.0.0:8080", "--workers", "2", "app:app"]
EOF

# Build and push to IBM Container Registry (ICR)
ibmcloud plugin install container-registry
ibmcloud cr login
ibmcloud cr namespace-add medassist-ns
docker build -t us.icr.io/medassist-ns/medassist:latest .
docker push us.icr.io/medassist-ns/medassist:latest
```

### Step 4 — Deploy to Code Engine

```bash
ibmcloud ce application create \
  --name medassist-app \
  --image us.icr.io/medassist-ns/medassist:latest \
  --cpu 0.5 \
  --memory 1G \
  --port 8080 \
  --min-scale 1 \
  --max-scale 3 \
  --env WATSONX_API_KEY=your_api_key \
  --env WATSONX_PROJECT_ID=your_project_id \
  --env WATSONX_URL=https://us-south.ml.cloud.ibm.com \
  --env WATSONX_MODEL_ID=ibm/granite-3-3-8b-instruct \
  --env FLASK_SECRET_KEY=your_secret_key
```

### Step 5 — Get your public URL

```bash
ibmcloud ce application get --name medassist-app --output url
```

---

## 🔒 Security Notes

- **Never** commit `.env` to git — add it to `.gitignore`
- Rotate your IBM Cloud API key periodically
- In production, set `FLASK_DEBUG=False` and `FLASK_ENV=production`
- Use IBM Secrets Manager for production credential storage
- Add `.env` to `.gitignore`:

```bash
echo ".env" >> .gitignore
```

---

## 🌐 Environment Variables Reference

| Variable | Required | Default | Description |
|---|---|---|---|
| `WATSONX_API_KEY` | ✅ Yes | — | IBM Cloud API key |
| `WATSONX_PROJECT_ID` | ✅ Yes | — | Watsonx.ai project ID |
| `WATSONX_URL` | ✅ Yes | us-south | Watsonx.ai endpoint URL |
| `WATSONX_MODEL_ID` | Optional | granite-3-3-8b-instruct | Granite model to use |
| `FLASK_SECRET_KEY` | ✅ Yes | — | Flask session secret (min 32 chars) |
| `FLASK_DEBUG` | Optional | True | Set False in production |
| `FLASK_PORT` | Optional | 5000 | Port to run on |
| `MAX_NEW_TOKENS` | Optional | 1024 | Max tokens per response |
| `TEMPERATURE` | Optional | 0.3 | Model temperature (0=focused, 1=creative) |

---

## ⚕️ Medical Disclaimer

MedAssist is an **educational tool only**.  
It does **NOT** diagnose, prescribe, or replace professional medical advice.  
Always consult a licensed physician for health concerns.  
For emergencies in India: **Call 108** (Ambulance)

---

## 📜 License

MIT License — see LICENSE file for details.

---

*Powered by IBM Watsonx.ai · Granite Models · Built with Flask & Bootstrap 5*
