# 🌍 StudyGlobal AI — Study Abroad Chatbot (Groq Edition)

AI-powered study abroad advisor for Indian & South Asian students,
built with **Streamlit** + **Groq API** (free & blazing fast).

---

## 📁 Project Structure

```
study_abroad_chatbot/
├── app.py                  ← Main Streamlit app
├── requirements.txt        ← Python dependencies
├── README.md               ← This file
└── .streamlit/
    └── config.toml         ← Dark theme config
```

---

## 🔑 Get Your Free Groq API Key

1. Go to https://console.groq.com
2. Sign up free → Create API Key
3. Copy the key (starts with `gsk_...`)

---

## 🖥️ Run Locally

```bash
# Install dependencies
pip install -r requirements.txt

# Run the app
streamlit run app.py
```

Opens at **http://localhost:8501** — paste your Groq API key in the sidebar.

---

## ☁️ Deploy Free on Streamlit Cloud

1. Push this folder to a **GitHub repo** (include `.streamlit/` folder)
2. Go to https://share.streamlit.io → Sign in → **New app**
3. Select repo → set `app.py` as main file → **Deploy**
4. In App Settings → **Secrets**, add:
   ```toml
   GROQ_API_KEY = "gsk_your_key_here"
   ```
   Then in `app.py` replace the `st.text_input` for api_key with:
   ```python
   api_key = st.secrets.get("GROQ_API_KEY", "")
   ```

---

## 🤖 Available Models

| Model | Speed | Best For |
|-------|-------|----------|
| Llama 3.3 70B | Fast | Best quality answers |
| Llama 3.1 8B | Fastest | Quick lookups |
| Mixtral 8x7B | Fast | Balanced |
| Gemma2 9B | Fast | Compact & efficient |

---

## 📚 Topics Covered

Application timeline · Tests (IELTS/TOEFL/GRE/GMAT) · SOP writing ·
Best universities (CS, Engineering, MBA, Data Science, Medicine, Arts) ·
Government & university scholarships · Apply without agent ·
Country-wise budget · Part-time jobs & salaries · Post-study visas ·
Pre-departure checklist
