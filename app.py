import streamlit as st
import requests
import json
import random
import smtplib
import time
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from groq import Groq

# ─── Page Config ─────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="StudyGlobal AI — Study Abroad Advisor",
    page_icon="🌍",
    layout="wide",
    
    initial_sidebar_state="expanded"
)

# ══════════════════════════════════════════════════════════════════════════════
#  🔧 CONFIGURATION — Fill these before running
# ══════════════════════════════════════════════════════════════════════════════

# ── Firebase Web API Key (from Firebase Console → Project Settings → General)
FIREBASE_API_KEY =  st.secrets.get("FIREBASE_API_KEY")  # 🔑 e.g. "AIzaSy..."

# ── Gmail credentials for sending OTP emails
SMTP_EMAIL    = "sandhiyamurali29@gmail.com"            # 📧 Gmail address
SMTP_PASSWORD = "fkcr yvih ucrl skdy"          # 🔐 Gmail App Password (not your login password)
# How to get App Password: Gmail → Settings → Security → 2FA ON → App Passwords → Generate

# ── Groq API Keys (add more to avoid rate limits)
GROQ_API_KEYS =st.secrets.get("GROQ_API_KEY")

# ══════════════════════════════════════════════════════════════════════════════
#  🔥 FIREBASE AUTH FUNCTIONS
# ══════════════════════════════════════════════════════════════════════════════

FIREBASE_BASE = "https://identitytoolkit.googleapis.com/v1/accounts"

def firebase_register(email: str, password: str):
    """Create a new Firebase user. Returns (user_data, error_message)."""
    url = f"{FIREBASE_BASE}:signUp?key={FIREBASE_API_KEY}"
    resp = requests.post(url, json={"email": email, "password": password, "returnSecureToken": True})
    data = resp.json()
    if "error" in data:
        msg = data["error"].get("message", "Registration failed")
        friendly = {
            "EMAIL_EXISTS": "This email is already registered. Please login.",
            "WEAK_PASSWORD : Password should be at least 6 characters": "Password must be at least 6 characters.",
            "INVALID_EMAIL": "Invalid email address.",
        }
        return None, friendly.get(msg, msg)
    return data, None

def firebase_login(email: str, password: str):
    """Login existing Firebase user. Returns (user_data, error_message)."""
    url = f"{FIREBASE_BASE}:signInWithPassword?key={FIREBASE_API_KEY}"
    resp = requests.post(url, json={"email": email, "password": password, "returnSecureToken": True})
    data = resp.json()
    if "error" in data:
        msg = data["error"].get("message", "Login failed")
        friendly = {
            "EMAIL_NOT_FOUND": "No account found with this email. Please register first.",
            "INVALID_PASSWORD": "Incorrect password. Please try again.",
            "INVALID_LOGIN_CREDENTIALS": "Invalid email or password.",
            "USER_DISABLED": "This account has been disabled.",
            "TOO_MANY_ATTEMPTS_TRY_LATER": "Too many failed attempts. Please try again later.",
        }
        return None, friendly.get(msg, msg)
    return data, None

def firebase_send_verification(id_token: str):
    """Send Firebase email verification link."""
    url = f"{FIREBASE_BASE}:sendOobCode?key={FIREBASE_API_KEY}"
    resp = requests.post(url, json={"requestType": "VERIFY_EMAIL", "idToken": id_token})
    return resp.json()

def firebase_get_user(id_token: str):
    """Get user profile to check email verification status."""
    url = f"{FIREBASE_BASE}:lookup?key={FIREBASE_API_KEY}"
    resp = requests.post(url, json={"idToken": id_token})
    data = resp.json()
    if "users" in data:
        return data["users"][0]
    return None

# ══════════════════════════════════════════════════════════════════════════════
#  📧 OTP EMAIL FUNCTIONS
# ══════════════════════════════════════════════════════════════════════════════

def generate_otp() -> str:
    return str(random.randint(100000, 999999))

def send_otp_email(to_email: str, otp: str, username: str = "") -> bool:
    """Send OTP via Gmail SMTP. Returns True on success."""
    try:
        msg = MIMEMultipart("alternative")
        msg["Subject"] = "🌍 StudyGlobal AI — Your OTP Verification Code"
        msg["From"]    = SMTP_EMAIL
        msg["To"]      = to_email

        html = f"""
        <div style="font-family:Arial,sans-serif;max-width:520px;margin:0 auto;background:#0c0f1a;border-radius:16px;overflow:hidden;">
          <div style="background:linear-gradient(135deg,#4f8ef7,#a78bfa);padding:32px;text-align:center;">
            <div style="font-size:48px;margin-bottom:8px;">🌍</div>
            <h1 style="color:#fff;margin:0;font-size:24px;font-weight:900;">StudyGlobal AI</h1>
            <p style="color:rgba(255,255,255,0.8);margin:6px 0 0;font-size:13px;">by Arjun Vision</p>
          </div>
          <div style="padding:32px;background:#131729;">
            <h2 style="color:#e8ecf5;font-size:20px;margin-top:0;">Verify Your Email</h2>
            <p style="color:#a0aac8;font-size:14px;line-height:1.6;">
              Hi {username or to_email.split('@')[0]},<br><br>
              Use the OTP below to complete your registration.
              This code expires in <strong style="color:#4f8ef7;">10 minutes</strong>.
            </p>
            <div style="background:#1a1f35;border:2px dashed #4f8ef7;border-radius:12px;padding:24px;text-align:center;margin:24px 0;">
              <div style="font-size:40px;font-weight:900;letter-spacing:10px;color:#4f8ef7;">{otp}</div>
              <p style="color:#7b87a8;font-size:12px;margin:8px 0 0;">One-Time Password</p>
            </div>
            <p style="color:#7b87a8;font-size:12px;line-height:1.6;">
              If you didn't request this, please ignore this email.<br>
              Do not share this OTP with anyone.
            </p>
          </div>
          <div style="background:#0a0f2c;padding:16px;text-align:center;">
            <p style="color:#4a5270;font-size:11px;margin:0;">
              © 2025 Arjun Vision · StudyGlobal AI · All rights reserved
            </p>
          </div>
        </div>
        """
        msg.attach(MIMEText(html, "html"))

        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
            server.login(SMTP_EMAIL, SMTP_PASSWORD)
            server.sendmail(SMTP_EMAIL, to_email, msg.as_string())
        return True
    except Exception as e:
        st.error(f"Email sending failed: {e}")
        return False

# ══════════════════════════════════════════════════════════════════════════════
#  🎨 CSS STYLES
# ══════════════════════════════════════════════════════════════════════════════

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Playfair+Display:wght@700;900&family=DM+Sans:wght@300;400;500;600&display=swap');
html, body, [class*="css"] { font-family: 'DM Sans', sans-serif; }
.stApp { background: linear-gradient(135deg,#0c0f1a 0%,#111428 50%,#0d1020 100%); }
[data-testid="stSidebar"] { background: rgba(13,15,30,0.97) !important; border-right:1px solid #252d4a; }
[data-testid="stSidebar"] * { color:#e8ecf5 !important; }
#MainMenu, footer, header { visibility:hidden; }
[data-testid="stChatMessage"] {
    background:rgba(26,31,53,0.8) !important;
    border:1px solid #252d4a !important;
    border-radius:16px !important;
    margin-bottom:12px !important;
}
.stButton > button {
    background:rgba(26,31,53,0.8) !important;
    border:1px solid #252d4a !important;
    border-radius:10px !important;
    color:#e8ecf5 !important;
    font-family:'DM Sans',sans-serif !important;
    font-size:13px !important;
    transition:all 0.2s ease !important;
    width:100% !important;
    text-align:left !important;
    padding:8px 12px !important;
}
.stButton > button:hover {
    background:rgba(79,142,247,0.15) !important;
    border-color:rgba(79,142,247,0.5) !important;
    color:#4f8ef7 !important;
}
[data-testid="stMetric"] {
    background:rgba(26,31,53,0.7) !important;
    border:1px solid #252d4a !important;
    border-radius:12px !important;
    padding:12px !important;
}
.stTextInput > div > div > input {
    background: rgba(26,31,53,0.9) !important;
    border: 1px solid #252d4a !important;
    border-radius: 10px !important;
    color: #e8ecf5 !important;
    font-family: 'DM Sans', sans-serif !important;
}
.stTextInput > div > div > input:focus {
    border-color: #4f8ef7 !important;
    box-shadow: 0 0 0 2px rgba(79,142,247,0.2) !important;
}
.auth-card {
    background: rgba(19,23,41,0.95);
    border: 1px solid #252d4a;
    border-radius: 20px;
    padding: 40px;
    max-width: 440px;
    margin: 40px auto;
}
.auth-title {
    font-family: 'Playfair Display', serif;
    font-size: 28px;
    font-weight: 900;
    background: linear-gradient(135deg,#e8ecf5,#a78bfa);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    background-clip: text;
    text-align: center;
    margin-bottom: 6px;
}
.auth-sub { color:#7b87a8; text-align:center; font-size:13px; margin-bottom:28px; }
.otp-box {
    background: rgba(79,142,247,0.08);
    border: 2px dashed rgba(79,142,247,0.4);
    border-radius: 12px;
    padding: 18px;
    text-align: center;
    margin: 16px 0;
}
.step-badge {
    display:inline-block;
    background:rgba(79,142,247,0.15);
    border:1px solid rgba(79,142,247,0.4);
    color:#4f8ef7;
    border-radius:20px;
    padding:3px 12px;
    font-size:11px;
    font-weight:600;
    letter-spacing:0.06em;
    margin-bottom:16px;
}
.stMarkdown, p, li, td, th { color:#c8d0e8 !important; }
h1, h2, h3 { color:#e8ecf5 !important; }
hr { border-color:#252d4a !important; }
::-webkit-scrollbar { width:5px; }
::-webkit-scrollbar-track { background:transparent; }
::-webkit-scrollbar-thumb { background:#252d4a; border-radius:10px; }
div[data-testid="stForm"] {
    background: transparent !important;
    border: none !important;
}
</style>
""", unsafe_allow_html=True)

# ══════════════════════════════════════════════════════════════════════════════
#  📚 KNOWLEDGE BASE
# ══════════════════════════════════════════════════════════════════════════════

KNOWLEDGE = """
You are StudyGlobal AI, a friendly and expert study abroad advisor specifically trained on the
"Study Abroad Complete Guide" for students from India and South Asia. You help students plan
their international education journey entirely without an education agent.

## APPLICATION TIMELINE
- 18-15 months before intake: Research programs on Mastersportal.eu / Bachelorsportal.eu, understand entry requirements, check English test registration deadlines.
- 15-12 months: Register and appear for IELTS/TOEFL/PTE. Register for GRE/GMAT if required. Start drafting resume and SOP outline.
- 12-9 months: Finalise university shortlist (2 ambitious + 5 target + 3 safe). Request official academic transcripts. Ask professors/managers for LORs.
- 9-6 months: Complete online applications on university portals. Pay application fees (USD 50-100 per university). Apply to scholarships simultaneously.
- 6-3 months: Compare offer letters. Accept preferred offer and pay tuition deposit. Apply for student visa on official government portal.
- 3-1 months: Book flights 60-90 days ahead. Open multi-currency account (Wise/Niyo Global). Arrange accommodation, travel insurance, forex card.
- Departure week: Carry originals + 3 photocopies. Store digital backups on Google Drive. Note university helpline and local emergency numbers.

## ENGLISH & STANDARDIZED TESTS
- IELTS Academic: UK, Australia, Canada, NZ — Minimum 6.0-7.0 — Valid 2 years
- TOEFL iBT: USA, Canada, Europe — Minimum 80-100 out of 120 — Valid 2 years
- PTE Academic: Australia, UK, Canada — Minimum 50-65 — Valid 2 years
- Duolingo English: Many US/EU universities — Minimum 100-120 — Valid 2 years
- GRE General: USA Graduate Programs — 310+ (Quant+Verbal) — Valid 5 years
- GMAT: MBA Programs worldwide — 600-720 — Valid 5 years
- SAT/ACT: USA Undergraduate — 1200+/26+ — Valid 5 years

## HOW TO WRITE A STRONG SOP
- Opening hook: short personal story (2-3 lines) about why this field matters
- Academic background: relevant coursework, final year projects, GPA
- Professional experience: internships, research, publications or freelance projects
- Why this specific university: mention professor's research, specific course, or lab
- Career goal: where you see yourself in 3 and 10 years
- Length: 700-1000 words. Always customise per university — never use a generic SOP.
- Get reviewed by 3 people: a subject expert, a language expert, and someone unfamiliar with your field.

## EXPERIENCE & INTERNSHIP CERTIFICATES
- Employment Letter: designation, duration, responsibilities, company seal & signature
- Internship Certificate: dates, company name, role, supervisor name & signature
- Research Certificate: lab/institute name, advisor, project title, duration
- Freelance Proof: client letters, invoices, tax documents, or online portfolio link
- Volunteer Certificate: organisation name, role, hours, supervisor sign
- Publication Proof: journal name, DOI, co-authors, acceptance/publication date
- Where to find internships: LinkedIn, Internshala, AngelList, Indeed, Glassdoor — apply 5+ per week
- International funded programs: Mitacs Globalink (Canada), DAAD WISE (Germany), SN Bose (USA)
- Virtual internships: Parker Dewey, Forage, Chegg Internships — valid and recognised
- Minimum: 1 internship (3-6 months) for Masters; 2-4 years full-time for MBA

## BEST UNIVERSITIES BY FIELD

### Computer Science & AI
- MIT (USA): World #1 in CS — cutting-edge AI and ML research
- Stanford University (USA): Silicon Valley connections, top AI & ML faculty
- ETH Zurich (Switzerland): Europe's best, near-zero tuition for all students
- University of Toronto (Canada): Affordable, strong AI research, great PR pathway
- University of Melbourne (Australia): Strong research culture, excellent PR route
- NUS / NTU (Singapore): Asia's top universities, English medium, global ranking

### Business & MBA
- Harvard Business School (USA): World #1 MBA — unmatched alumni and brand value
- London Business School (UK): Europe's top MBA, diverse global cohort
- INSEAD (France/Singapore): Prestigious 1-year MBA, fastest ROI
- Schulich School at York University (Canada): Affordable MBA with strong PR opportunities
- UNSW Business School (Australia): Strong alumni network, industry-linked curriculum

### Engineering
- TU Munich — TUM (Germany): Europe's top engineering university — tuition FREE
- Delft University of Technology (Netherlands): World-class engineering, English programs
- Imperial College London (UK): Top 10 globally for Engineering
- University of Waterloo (Canada): Co-op program, direct industry experience
- RMIT / Monash University (Australia): Industry-linked programs, strong job market

### Data Science & Analytics
- Carnegie Mellon University (USA): Ranked #1 for MSML and MSDS programs
- Columbia University (USA): NYC location — direct access to finance and tech firms
- University of Amsterdam (Netherlands): Strong AI/DS program, affordable EU living
- University of British Columbia (Canada): Excellent DS MSc, great job market
- Monash University (Australia): Applied Data Science, clear PR pathway

### Medicine & Public Health
- Johns Hopkins University (USA): Global leader in public health and medicine
- University of Edinburgh (UK): UK's top medical school, strong research output
- University of Queensland (Australia): MBBS open to international students
- Maastricht University (Netherlands): Problem-based learning, affordable fees
- Karolinska Institute (Sweden): Nobel Prize in Medicine awarded here — world-class

### Arts, Design & Architecture
- Royal College of Art (UK): Ranked world #1 for Art & Design consistently
- Pratt Institute (USA): Top choice for Architecture and Industrial Design
- Politecnico di Milano (Italy): Design & Architecture excellence at low EU fees
- RMIT University (Australia): Leading creative industries school in Asia-Pacific
- Aalto University (Finland): Unique fusion of Design, Technology and Business

## GOVERNMENT SCHOLARSHIPS
- Chevening (UK): Full tuition + living + flights — Requires 2 years work experience
- Commonwealth Masters (UK): Full tuition + monthly stipend — Citizens of developing countries
- Fulbright-Nehru (USA): Full tuition + stipend + travel — Indian citizens only
- DAAD 60+ programs (Germany): Tuition + monthly EUR 850-1,200 — Strong academics
- Eiffel Excellence (France): Tuition + EUR 1,181/month — Under 30 years, excellent grades
- Erasmus Mundus (EU): Full tuition + EUR 1,400/month — Joint EU Masters programs
- Australia Awards: Full tuition + living allowance — Citizens of developing countries
- Vanier Canada Graduate: CAD 50,000/year for 3 years — PhD students
- Swedish Institute: Full tuition + SEK 11,000/month — Developing country citizens

## UNIVERSITY SCHOLARSHIPS
- University of Toronto — Lester B. Pearson: Full tuition + living — Deadline: Nov-Jan
- University of Edinburgh — Global Online Scholarship: 50% tuition — Rolling
- McGill University — Entrance Award: CAD 3,000-10,000 — Deadline: Jan 15
- University of Melbourne — Graduate Research: Full + AUD 32,000/year — Oct-Nov
- TU Munich — Deutschlandstipendium: EUR 300/month — Varies by program
- NUS Singapore — Research Scholarship: Full + SGD 2,000/month — Annual
- ETH Zurich — Excellence Scholarship: Full + CHF 12,000/year — Dec 15
- University of Amsterdam — Holland Scholarship: EUR 5,000 one-time — Feb 1
- Monash University — International Merit: AUD 10,000/year — Rolling

## APPLYING WITHOUT AN AGENT
Agents charge INR 50,000-2,00,000 for services you can do FREE:
- University shortlisting: topuniversities.com / timeshighereducation.com
- SOP editing: Reddit r/gradadmissions (free)
- Document verification: wes.org (self-service)
- Visa guidance: VFS Global / UKVI / IRCC.canada.ca
- Scholarship search: scholars4dev.com / scholarshipportal.eu

Steps: 1) Research on Mastersportal.eu 2) Check eligibility on university website 3) Apply via UCAS/Common App/OUAC 4) Upload docs as PDF 5) Pay fees via Wise card 6) Track in spreadsheet 7) Accept offer 8) Apply visa directly

## DOCUMENTS TO CARRY
- Identity: Passport (18+ months valid), Aadhaar, PAN card
- Academic: All degree certificates, mark sheets, transcripts
- Admission: Offer letter, CoE/CAS/I-20
- Financial: Bank statements (12 months), scholarship letter, loan sanction
- Health: Medical insurance, vaccination records, prescription in English
- Pre-departure: Open Wise/Niyo Global account, carry USD 500-1000 cash, buy 12-month travel insurance, register at madad.gov.in

## ANNUAL BUDGET (Masters Level)
USA: Tuition $25,000-55,000 | Living $17,000-30,000 | TOTAL $45,000-94,500
UK: Tuition £15,000-35,000 | Living £12,000-22,000 | TOTAL £28,824-61,000
Canada: Tuition CAD 18,000-35,000 | Living CAD 14,000-24,000 | TOTAL CAD 33,800-63,500
Australia: Tuition AUD 28,000-45,000 | Living AUD 22,000-32,000 | TOTAL AUD 50,600-83,400
Germany: Tuition EUR 0-3,000 (FREE at public unis) | Living EUR 8,000-15,000 | TOTAL EUR 10,000-21,000

One-Time Pre-Departure (INR): Flight 40,000-90,000 | Visa 10,000-25,000 | Exams 15,000-30,000 | Forex 1,50,000-2,50,000

## PART-TIME WORK RIGHTS
- USA: 20 hrs/week on-campus, OPT 12 months, STEM OPT 36 months
- UK: 20 hrs/week, Graduate Route Visa 2-3 years
- Canada: 20 hrs/week, PGWP up to 3 years
- Australia: 48 hrs/fortnight, Post-Study Work Visa 2-6 years
- Germany: 120 full or 240 half days/year, 18-month job seeker visa

## PART-TIME JOB PAY
- On-campus jobs: USD/AUD/CAD 12-18/hr
- Restaurant/cafe/retail: GBP 12-14 / EUR 10-15/hr
- Private tutoring: USD 15-25/hr
- Freelance tech (Upwork/Fiverr): USD 15-80/hr (remote)
- Research assistant: USD 15-20/hr

## EXPECTED SALARIES (Masters)
- CS/AI: USA $90,000-150,000 | UK £45,000-80,000 | Canada CAD 75,000-120,000 | Australia AUD 85,000-130,000
- Data Science: USA $85,000-130,000 | UK £40,000-70,000 | Canada CAD 70,000-110,000
- Engineering: USA $75,000-110,000 | UK £35,000-60,000 | Canada CAD 65,000-100,000
- MBA/Business: USA $90,000-140,000 | UK £45,000-80,000 | Canada CAD 70,000-110,000
- Healthcare: USA $60,000-100,000 | UK £32,000-55,000 | Canada CAD 55,000-90,000

Instructions:
- Answer ONLY based on the knowledge above. Be friendly and well structured.
- Use markdown: **bold**, bullet points, tables, headers.
- For tips use > blockquote format.
- Do not make up information not in the guide.
"""

# ══════════════════════════════════════════════════════════════════════════════
#  📋 TOPIC / QUICK QUESTION LISTS
# ══════════════════════════════════════════════════════════════════════════════

GROQ_MODELS = {
    "⚡ Llama 3.3 70B  (Best)":   "llama-3.3-70b-versatile",
    "🚀 Llama 3.1 8B   (Fastest)": "llama-3.1-8b-instant",
    "🔀 Mixtral 8x7B":             "mixtral-8x7b-32768",
    "💎 Gemma2 9B":                "gemma2-9b-it",
}

TOPICS = [
    ("📅", "Application Timeline",    "What is the complete application timeline for studying abroad?"),
    ("📝", "Tests & Scores",          "What English and standardized tests do I need for studying abroad?"),
    ("✍️", "Writing Your SOP",        "How do I write a strong Statement of Purpose (SOP)?"),
    ("📜", "Certificates & Exp.",     "What internship and experience certificates do I need?"),
    ("💻", "CS & AI Universities",    "What are the best universities for Computer Science and AI?"),
    ("⚙️", "Engineering Unis",        "What are the best universities for Engineering?"),
    ("💼", "MBA & Business",          "What are the best MBA programs abroad?"),
    ("📊", "Data Science",            "What are the best universities for Data Science?"),
    ("🏆", "Govt Scholarships",       "Tell me about government scholarships available for Indian students."),
    ("🎓", "University Scholarships", "What university-specific scholarships can I apply for?"),
    ("🚀", "Apply Without Agent",     "How can I apply to universities without an education agent?"),
    ("📁", "Documents Checklist",     "What documents do I need to carry when going abroad for studies?"),
    ("💰", "Full Cost Budget",        "What is the full budget for studying abroad including tuition and living costs?"),
    ("👷", "Part-Time Jobs",          "What are the part-time job opportunities and salary for students abroad?"),
    ("🌐", "Post-Study Visas",        "What are the post-study work visa options for different countries?"),
    ("✅", "Master Checklist",        "Give me the complete pre-departure checklist."),
]

QUICK_QUESTIONS = [
    ("🌏", "Best countries & costs",    "What are the best countries to study abroad for Indian students and their approximate annual costs?"),
    ("🏆", "Fully funded scholarships", "What scholarships are fully funded for Indian students?"),
    ("🚀", "Apply without an agent",    "How do I apply to universities without paying an agent? Give me step-by-step guidance."),
    ("💰", "Salary after graduation",   "What is the expected salary after graduation for CS and Data Science in USA, UK, and Canada?"),
]

# ══════════════════════════════════════════════════════════════════════════════
#  🔐 SESSION STATE INIT
# ══════════════════════════════════════════════════════════════════════════════

defaults = {
    "logged_in":        False,
    "user_email":       "",
    "user_name":        "",
    "id_token":         "",
    "auth_page":        "login",       # "login" | "register" | "verify_otp"
    "otp_code":         "",
    "otp_expiry":       0,
    "otp_email":        "",
    "reg_password":     "",
    "messages":         [],
    "pending_question": None,
}
for k, v in defaults.items():
    if k not in st.session_state:
        st.session_state[k] = v

# ══════════════════════════════════════════════════════════════════════════════
#  🔑 AUTH PAGES
# ══════════════════════════════════════════════════════════════════════════════

def show_auth_header():
    st.markdown("""
    <div style='text-align:center;padding:30px 0 10px;'>
        <div style='font-size:52px;margin-bottom:8px;'>🌍</div>
        <div style='font-family:Playfair Display,serif;font-size:30px;font-weight:900;
                    background:linear-gradient(90deg,#4f8ef7,#a78bfa);
                    -webkit-background-clip:text;-webkit-text-fill-color:transparent;
                    background-clip:text;'>
            StudyGlobal AI
        </div>
        <div style='font-size:12px;color:#7b87a8;margin-top:4px;letter-spacing:0.1em;text-transform:uppercase;'>
            by Sandhiya
        </div>
    </div>
    """, unsafe_allow_html=True)


def page_login():
    show_auth_header()
    _, col, _ = st.columns([1, 2, 1])
    with col:
        st.markdown('<div class="auth-card">', unsafe_allow_html=True)
        st.markdown('<div class="step-badge">SIGN IN</div>', unsafe_allow_html=True)
        st.markdown('<div class="auth-title">Welcome Back 👋</div>', unsafe_allow_html=True)
        st.markdown('<div class="auth-sub">Login with your registered email and password</div>', unsafe_allow_html=True)

        with st.form("login_form"):
            email    = st.text_input("📧 Email Address", placeholder="you@gmail.com")
            password = st.text_input("🔐 Password", type="password", placeholder="Your password")
            submit   = st.form_submit_button("Login →", use_container_width=True)

        if submit:
            if not email or not password:
                st.error("Please fill in all fields.")
            else:
                with st.spinner("Signing in..."):
                    user, err = firebase_login(email.strip(), password)
                if err:
                    st.error(f"❌ {err}")
                else:
                    st.session_state.logged_in   = True
                    st.session_state.user_email  = user["email"]
                    st.session_state.id_token    = user["idToken"]
                    st.session_state.user_name   = user.get("displayName", email.split("@")[0])
                    st.success("✅ Login successful! Loading your dashboard...")
                    time.sleep(1)
                    st.rerun()

        st.markdown("<br>", unsafe_allow_html=True)
        st.markdown('<div style="text-align:center;color:#7b87a8;font-size:13px;">Don\'t have an account?</div>', unsafe_allow_html=True)
        if st.button("➕  Create a new account", use_container_width=True):
            st.session_state.auth_page = "register"
            st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)


def page_register():
    show_auth_header()
    _, col, _ = st.columns([1, 2, 1])
    with col:
        st.markdown('<div class="auth-card">', unsafe_allow_html=True)
        st.markdown('<div class="step-badge">STEP 1 OF 2 — CREATE ACCOUNT</div>', unsafe_allow_html=True)
        st.markdown('<div class="auth-title">Create Account 🚀</div>', unsafe_allow_html=True)
        st.markdown('<div class="auth-sub">Register with your email. We\'ll send you a 6-digit OTP to verify.</div>', unsafe_allow_html=True)

        with st.form("register_form"):
            name     = st.text_input("👤 Full Name",     placeholder="Your name")
            email    = st.text_input("📧 Email Address", placeholder="you@gmail.com")
            password = st.text_input("🔐 Password",      type="password", placeholder="Min 6 characters")
            confirm  = st.text_input("🔐 Confirm Password", type="password", placeholder="Repeat password")
            submit   = st.form_submit_button("Send OTP to Email →", use_container_width=True)

        if submit:
            if not all([name, email, password, confirm]):
                st.error("Please fill in all fields.")
            elif len(password) < 6:
                st.error("Password must be at least 6 characters.")
            elif password != confirm:
                st.error("Passwords do not match.")
            else:
                with st.spinner("Creating your account & sending OTP..."):
                    user, err = firebase_register(email.strip(), password)
                    if err:
                        st.error(f"❌ {err}")
                    else:
                        otp = generate_otp()
                        sent = send_otp_email(email.strip(), otp, name)
                        if sent:
                            st.session_state.otp_code    = otp
                            st.session_state.otp_expiry  = time.time() + 600  # 10 min
                            st.session_state.otp_email   = email.strip()
                            st.session_state.reg_password = password
                            st.session_state.id_token    = user["idToken"]
                            st.session_state.user_name   = name
                            st.session_state.auth_page   = "verify_otp"
                            st.success("✅ OTP sent! Check your email.")
                            time.sleep(1)
                            st.rerun()
                        else:
                            st.error("Failed to send OTP. Check your SMTP settings.")

        st.markdown("<br>", unsafe_allow_html=True)
        st.markdown('<div style="text-align:center;color:#7b87a8;font-size:13px;">Already have an account?</div>', unsafe_allow_html=True)
        if st.button("🔑  Go to Login", use_container_width=True):
            st.session_state.auth_page = "login"
            st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)


def page_verify_otp():
    show_auth_header()
    _, col, _ = st.columns([1, 2, 1])
    with col:
        st.markdown('<div class="auth-card">', unsafe_allow_html=True)
        st.markdown('<div class="step-badge">STEP 2 OF 2 — VERIFY EMAIL</div>', unsafe_allow_html=True)
        st.markdown('<div class="auth-title">Verify Your Email ✉️</div>', unsafe_allow_html=True)

        email = st.session_state.otp_email
        remaining = int(st.session_state.otp_expiry - time.time())

        if remaining > 0:
            mins, secs = divmod(remaining, 60)
            st.markdown(f"""
            <div class="otp-box">
                <div style='color:#4f8ef7;font-size:13px;margin-bottom:6px;'>OTP sent to</div>
                <div style='color:#e8ecf5;font-size:15px;font-weight:600;'>{email}</div>
                <div style='color:#7b87a8;font-size:12px;margin-top:8px;'>
                    Expires in <span style='color:#f5c842;font-weight:700;'>{mins:02d}:{secs:02d}</span>
                </div>
            </div>
            """, unsafe_allow_html=True)
        else:
            st.error("⏰ OTP has expired. Please register again.")
            if st.button("← Back to Register"):
                st.session_state.auth_page = "register"
                st.rerun()
            st.markdown('</div>', unsafe_allow_html=True)
            return

        with st.form("otp_form"):
            entered_otp = st.text_input("🔢 Enter 6-digit OTP", placeholder="e.g. 482910", max_chars=6)
            verify_btn  = st.form_submit_button("✅  Verify & Login", use_container_width=True)

        if verify_btn:
            if not entered_otp:
                st.error("Please enter the OTP.")
            elif time.time() > st.session_state.otp_expiry:
                st.error("OTP expired. Please register again.")
            elif entered_otp.strip() != st.session_state.otp_code:
                st.error("❌ Incorrect OTP. Please try again.")
            else:
                # OTP verified — log the user in
                user, err = firebase_login(email, st.session_state.reg_password)
                if err:
                    st.error(f"Login error: {err}")
                else:
                    st.session_state.logged_in   = True
                    st.session_state.user_email  = email
                    st.session_state.id_token    = user["idToken"]
                    st.session_state.otp_code    = ""
                    st.success("🎉 Email verified! Welcome to StudyGlobal AI!")
                    time.sleep(1)
                    st.rerun()

        st.markdown("<br>", unsafe_allow_html=True)

        # Resend OTP
        col1, col2 = st.columns(2)
        with col1:
            if st.button("🔄  Resend OTP", use_container_width=True):
                new_otp = generate_otp()
                sent = send_otp_email(email, new_otp, st.session_state.user_name)
                if sent:
                    st.session_state.otp_code   = new_otp
                    st.session_state.otp_expiry = time.time() + 600
                    st.success("New OTP sent!")
                    time.sleep(1)
                    st.rerun()
        with col2:
            if st.button("← Back to Register", use_container_width=True):
                st.session_state.auth_page = "register"
                st.rerun()

        st.markdown('</div>', unsafe_allow_html=True)

# ══════════════════════════════════════════════════════════════════════════════
#  💬 GROQ CHAT FUNCTIONS
# ══════════════════════════════════════════════════════════════════════════════

def call_groq(keys, model: str, history: list) -> str:
    if isinstance(keys, str):
        keys = [keys]
    api_msgs = [{"role": "system", "content": KNOWLEDGE}] + [
        {"role": m["role"], "content": m["content"]} for m in history
    ]
    last_error = None
    for key in keys:
        try:
            client = Groq(api_key=key)
            resp = client.chat.completions.create(
                model=model, messages=api_msgs, max_tokens=1024, temperature=0.7
            )
            return resp.choices[0].message.content
        except Exception as e:
            last_error = e
            if "429" in str(e) or "rate_limit" in str(e).lower():
                continue
            raise e
    raise Exception(f"All API keys hit rate limits. Wait ~30 min or add more keys.\n\n{last_error}")

def handle(question: str, model_id: str):
    st.session_state.messages.append({"role": "user", "content": question})
    with st.chat_message("user", avatar="👤"):
        st.markdown(question)
    with st.chat_message("assistant", avatar="🌍"):
        with st.spinner("Thinking..."):
            try:
                reply = call_groq(GROQ_API_KEYS, model_id, st.session_state.messages)
                st.markdown(reply)
                st.session_state.messages.append({"role": "assistant", "content": reply})
            except Exception as e:
                reply = f"❌ **Error:** {e}"
                st.error(reply)
                st.session_state.messages.append({"role": "assistant", "content": reply})

# ══════════════════════════════════════════════════════════════════════════════
#  🖥️ MAIN APP ROUTER
# ══════════════════════════════════════════════════════════════════════════════

if not st.session_state.logged_in:
    # ── Show Auth Pages ──────────────────────────────────────────────────────
    page = st.session_state.auth_page
    if page == "login":
        page_login()
    elif page == "register":
        page_register()
    elif page == "verify_otp":
        page_verify_otp()

else:
    # ══════════════════════════════════════════════════════════════════════════
    #  ✅ LOGGED IN — SHOW CHATBOT
    # ══════════════════════════════════════════════════════════════════════════

    # ── Sidebar ───────────────────────────────────────────────────────────────
    with st.sidebar:
        st.markdown(f"""
        <div style='text-align:center;padding:10px 0 20px;'>
            <div style='font-size:46px;'>🌍</div>
            <div style='font-family:Playfair Display,serif;font-size:20px;font-weight:900;
                        background:linear-gradient(90deg,#4f8ef7,#a78bfa);
                        -webkit-background-clip:text;-webkit-text-fill-color:transparent;background-clip:text;'>
                StudyGlobal AI
            </div>
            <div style='font-size:11px;color:#7b87a8;margin-top:4px;'>Powered by Groq</div>
        </div>
        <div style='background:rgba(79,142,247,0.1);border:1px solid rgba(79,142,247,0.3);
                    border-radius:10px;padding:10px 14px;margin-bottom:16px;'>
            <div style='font-size:11px;color:#7b87a8;'>Logged in as</div>
            <div style='font-size:13px;color:#4f8ef7;font-weight:600;word-break:break-all;'>
                {st.session_state.user_email}
            </div>
        </div>
        """, unsafe_allow_html=True)

        st.markdown("**🤖 Model**")
        model_label = st.selectbox("Model", list(GROQ_MODELS.keys()), index=0, label_visibility="collapsed")
        model_id = GROQ_MODELS[model_label]

        st.markdown("---")

        col1, col2 = st.columns(2)
        with col1:
            if st.button("🗑️ Clear Chat", use_container_width=True):
                st.session_state.messages = []
                st.rerun()
        with col2:
            if st.button("🚪 Logout", use_container_width=True):
                for key in list(defaults.keys()):
                    st.session_state[key] = defaults[key]
                st.rerun()

        st.markdown("---")
        st.markdown('<div style="font-size:11px;color:#7b87a8;text-transform:uppercase;letter-spacing:0.08em;margin-bottom:10px;">Browse Topics</div>', unsafe_allow_html=True)

        for icon, label, question in TOPICS:
            if st.button(f"{icon}  {label}", key=f"t_{label}"):
                st.session_state.pending_question = question

        st.markdown("---")
        st.markdown("""
        <div style='font-size:11px;color:#7b87a8;line-height:1.7;'>
            📌 Based on the <strong style='color:#a78bfa;'>Study Abroad Complete Guide</strong>
            for Indian & South Asian students.<br><br>
            <strong style='color:#4f8ef7;'>Key Resources:</strong><br>
            mastersportal.eu · scholars4dev.com<br>daad.de · chevening.org
        </div>
        """, unsafe_allow_html=True)

    # ── Main area ─────────────────────────────────────────────────────────────
    st.markdown(f"""
    <div style='padding:20px 0 10px;'>
        <h1 style='font-family:Playfair Display,serif;font-size:30px;font-weight:900;margin:0;
                   background:linear-gradient(135deg,#e8ecf5,#a78bfa);
                   -webkit-background-clip:text;-webkit-text-fill-color:transparent;background-clip:text;'>
            Welcome, {st.session_state.user_name}! 🎓
        </h1>
        <p style='color:#7b87a8;font-size:14px;margin-top:6px;'>
            Ask me anything about universities, scholarships, budgets, visas, and jobs — for Indian students.
        </p>
    </div>
    """, unsafe_allow_html=True)

    c1, c2, c3, c4 = st.columns(4)
    with c1: st.metric("Countries Covered", "7+",   "USA, UK, CA, AU, DE...")
    with c2: st.metric("Scholarships",      "18+",  "Fully funded options")
    with c3: st.metric("Universities",      "35+",  "Across all fields")
    with c4: st.metric("Agent Cost Saved",  "₹2L+", "100% DIY guidance")

    st.markdown("---")

    # Welcome quick buttons (only when no messages yet)
    if not st.session_state.messages:
        st.markdown("""
        <div style='text-align:center;padding:16px 0 20px;'>
            <div style='font-size:46px;margin-bottom:10px;'>✈️</div>
            <div style='font-size:17px;color:#e8ecf5;font-weight:600;margin-bottom:6px;'>
                What would you like to know today?
            </div>
            <div style='font-size:13px;color:#7b87a8;'>Click a question below or browse topics in the sidebar</div>
        </div>
        """, unsafe_allow_html=True)

        col_a, col_b = st.columns(2)
        for i, (icon, label, question) in enumerate(QUICK_QUESTIONS):
            with (col_a if i % 2 == 0 else col_b):
                if st.button(f"{icon}  {label}", key=f"q_{i}", use_container_width=True):
                    st.session_state.pending_question = question

    # Chat history
    for msg in st.session_state.messages:
        with st.chat_message(msg["role"], avatar="🌍" if msg["role"] == "assistant" else "👤"):
            st.markdown(msg["content"])

    # Handle sidebar/quick button clicks
    if st.session_state.pending_question:
        q = st.session_state.pending_question
        st.session_state.pending_question = None
        handle(q, model_id)
        st.rerun()

    # Chat input
    if prompt := st.chat_input("Ask about universities, scholarships, budget, visas, jobs..."):
        handle(prompt, model_id)
