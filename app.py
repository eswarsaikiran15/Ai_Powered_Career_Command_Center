import streamlit as st
import os
from dotenv import load_dotenv

load_dotenv()

# Must be first Streamlit call
st.set_page_config(
    page_title="AI Career Command Center",
    page_icon="🚀",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ── Validate API Key ──────────────────────────────────────────────────────────
API_KEY = os.getenv("GROQ_API_KEY", "")
if not API_KEY or "your_groq" in API_KEY:
    st.error("❌ GROQ_API_KEY not configured. Copy `.env.example` to `.env` and add your key.")
    st.markdown("""
    **Quick Setup:**
    1. Get a free key at [console.groq.com](https://console.groq.com)
    2. Copy `.env.example` → `.env`
    3. Add your key: `GROQ_API_KEY=gsk_...`
    4. Restart the app
    """)
    st.stop()

# ── Init DB ───────────────────────────────────────────────────────────────────
from utils.db import init_db
init_db()

# ── CSS ───────────────────────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@300;400;500;600;700&family=JetBrains+Mono:wght@400;700&display=swap');

html, body, [class*="css"] {
    font-family: 'Space Grotesk', sans-serif;
}

/* Dark background */
.stApp {
    background: #0d1117;
    color: #e6edf3;
}

/* Sidebar */
[data-testid="stSidebar"] {
    background: #161b22 !important;
    border-right: 1px solid #30363d;
}

/* Main header */
.main-header {
    background: linear-gradient(135deg, #1a1f35 0%, #0d1117 50%, #1a1f35 100%);
    border: 1px solid #30363d;
    border-radius: 16px;
    padding: 2rem;
    margin-bottom: 2rem;
    text-align: center;
    position: relative;
    overflow: hidden;
}

.main-header::before {
    content: '';
    position: absolute;
    top: -50%;
    left: -50%;
    width: 200%;
    height: 200%;
    background: radial-gradient(circle, rgba(88,166,255,0.05) 0%, transparent 60%);
    animation: pulse 4s ease-in-out infinite;
}

@keyframes pulse {
    0%, 100% { transform: scale(1); opacity: 0.5; }
    50% { transform: scale(1.1); opacity: 1; }
}

.main-title {
    font-size: 2.8rem;
    font-weight: 700;
    background: linear-gradient(135deg, #58a6ff, #bc8cff, #ff7b72);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    background-clip: text;
    margin: 0;
    line-height: 1.2;
}

.main-subtitle {
    color: #8b949e;
    font-size: 1rem;
    margin-top: 0.5rem;
}

/* Nav cards */
.nav-card {
    background: #161b22;
    border: 1px solid #30363d;
    border-radius: 12px;
    padding: 1.2rem;
    text-align: center;
    cursor: pointer;
    transition: all 0.2s ease;
    margin-bottom: 8px;
}

.nav-card:hover {
    border-color: #58a6ff;
    background: #1c2128;
    transform: translateY(-2px);
}

.nav-card.active {
    border-color: #58a6ff;
    background: linear-gradient(135deg, #1c2128, #1a2035);
    box-shadow: 0 0 20px rgba(88,166,255,0.1);
}

/* Metrics */
[data-testid="metric-container"] {
    background: #161b22;
    border: 1px solid #30363d;
    border-radius: 10px;
    padding: 1rem;
}

/* Buttons */
.stButton > button {
    background: linear-gradient(135deg, #238636, #2ea043);
    color: white;
    border: none;
    border-radius: 8px;
    font-family: 'Space Grotesk', sans-serif;
    font-weight: 600;
    transition: all 0.2s ease;
}

.stButton > button:hover {
    background: linear-gradient(135deg, #2ea043, #3fb950);
    transform: translateY(-1px);
    box-shadow: 0 4px 15px rgba(46,160,67,0.3);
}

.stButton > button[kind="primary"] {
    background: linear-gradient(135deg, #1f6feb, #388bfd);
}

.stButton > button[kind="primary"]:hover {
    background: linear-gradient(135deg, #388bfd, #58a6ff);
    box-shadow: 0 4px 15px rgba(88,166,255,0.3);
}

/* Text areas */
textarea, input {
    background: #161b22 !important;
    color: #e6edf3 !important;
    border-color: #30363d !important;
    border-radius: 8px !important;
    font-family: 'Space Grotesk', sans-serif !important;
}

/* Expanders */
[data-testid="stExpander"] {
    background: #161b22;
    border: 1px solid #30363d;
    border-radius: 8px;
}

/* Success/Info/Warning/Error */
.stSuccess {
    background: rgba(46,160,67,0.1) !important;
    border: 1px solid rgba(46,160,67,0.3) !important;
    border-radius: 8px !important;
}

.stInfo {
    background: rgba(88,166,255,0.1) !important;
    border: 1px solid rgba(88,166,255,0.3) !important;
    border-radius: 8px !important;
}

/* Tabs */
[data-testid="stTabs"] button {
    font-family: 'Space Grotesk', sans-serif;
    font-weight: 500;
}

/* Divider */
hr {
    border-color: #30363d !important;
}

/* Code/mono */
code {
    font-family: 'JetBrains Mono', monospace;
    background: #161b22;
    padding: 2px 6px;
    border-radius: 4px;
    color: #ff7b72;
}

/* Sidebar active module */
.sidebar-module {
    padding: 0.6rem 1rem;
    border-radius: 8px;
    margin: 4px 0;
    cursor: pointer;
    font-weight: 500;
    transition: all 0.15s ease;
    border: 1px solid transparent;
}

.sidebar-module:hover {
    background: #1c2128;
    border-color: #30363d;
}

.sidebar-module.active {
    background: linear-gradient(135deg, #1c2128, #1a2035);
    border-color: #58a6ff;
    color: #58a6ff;
}

/* Status badge */
.status-badge {
    display: inline-block;
    padding: 2px 10px;
    border-radius: 20px;
    font-size: 0.75rem;
    font-weight: 600;
}

.status-free {
    background: rgba(46,160,67,0.2);
    color: #3fb950;
    border: 1px solid rgba(46,160,67,0.3);
}
</style>
""", unsafe_allow_html=True)

# ── Session State ─────────────────────────────────────────────────────────────
if "active_module" not in st.session_state:
    st.session_state.active_module = "home"

# ── Sidebar Navigation ────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("""
    <div style="text-align:center;padding:1rem 0;">
        <div style="font-size:2rem;">🚀</div>
        <div style="font-weight:700;font-size:1.1rem;color:#e6edf3;">Career Command</div>
        <div style="font-size:0.75rem;color:#8b949e;">AI-Powered Job Search OS</div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("---")

    modules = [
        ("home",        "🏠", "Home Dashboard"),
        ("resume",      "📄", "Resume Analyzer"),
        ("trends",      "📈", "Skill Trends"),
        ("interview",   "🎤", "Interview Coach"),
        ("cover",       "✉️",  "Cover Letter"),
        ("salary",      "💰", "Salary Estimator"),
        ("briefing",    "📰", "Daily Briefing"),
        ("github",      "🐙", "GitHub Analyzer"),
        ("roadmap",     "🗺️", "Learning Roadmap"),
    ]

    for key, icon, label in modules:
        active_style = "background:#1c2128;border:1px solid #58a6ff;color:#58a6ff;" if st.session_state.active_module == key else ""
        if st.button(f"{icon}  {label}", key=f"nav_{key}", use_container_width=True):
            st.session_state.active_module = key
            st.rerun()

    st.markdown("---")

    # API Status
    st.markdown("### ⚙️ API Status")
    st.markdown(f'<span class="status-badge status-free">✅ Groq Connected</span>', unsafe_allow_html=True)

    news_key = os.getenv("NEWS_API_KEY", "")
    tg_token = os.getenv("TELEGRAM_BOT_TOKEN", "")
    gh_token = os.getenv("GITHUB_TOKEN", "")

    statuses = [
        ("NewsAPI", bool(news_key and "your_news" not in news_key)),
        ("Telegram", bool(tg_token and "your_tele" not in tg_token)),
        ("GitHub Token", bool(gh_token and "your_git" not in gh_token)),
    ]
    for name, connected in statuses:
        badge = f'<span class="status-badge status-free">✅ {name}</span>' if connected else \
                f'<span style="background:rgba(248,81,73,0.15);color:#f85149;border:1px solid rgba(248,81,73,0.3);padding:2px 10px;border-radius:20px;font-size:0.75rem;">⚪ {name} (optional)</span>'
        st.markdown(badge, unsafe_allow_html=True)
        st.markdown("")

    st.markdown("---")
    st.markdown('<p style="color:#8b949e;font-size:0.75rem;text-align:center;">Built by Kamparapu Eswar Sai Kiran<br/>Zero cost · Open source</p>',
                unsafe_allow_html=True)

# ── Main Content ──────────────────────────────────────────────────────────────
module = st.session_state.active_module

if module == "home":
    st.markdown("""
    <div class="main-header">
        <h1 class="main-title">🚀 AI Career Command Center</h1>
        <p class="main-subtitle">Your intelligent job search operating system — 8 AI-powered tools, zero cost, 100% free APIs</p>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("### 🛠️ Your Career Toolkit")
    tools = [
        ("📄", "Resume Analyzer", "Match score, skill gaps, ATS check, improvement tips", "resume"),
        ("📈", "Skill Trends", "Live job market demand from HackerNews + AI analysis", "trends"),
        ("🎤", "Interview Coach", "Role-specific questions with answer frameworks", "interview"),
        ("✉️", "Cover Letter", "3 versions + cold email + LinkedIn message", "cover"),
        ("💰", "Salary Estimator", "Compare salaries across countries with real economic data", "salary"),
        ("📰", "Daily Briefing", "AI-written tech career briefing + Telegram delivery", "briefing"),
        ("🐙", "GitHub Analyzer", "Profile score, improvement tips, project suggestions", "github"),
        ("🗺️", "Learning Roadmap", "Week-by-week plan from your JDs + progress tracking", "roadmap"),
    ]

    cols = st.columns(4)
    for i, (icon, name, desc, key) in enumerate(tools):
        with cols[i % 4]:
            st.markdown(f"""
            <div style="background:#161b22;border:1px solid #30363d;border-radius:12px;
            padding:1.2rem;text-align:center;margin-bottom:1rem;min-height:160px;">
                <div style="font-size:2rem;margin-bottom:0.5rem;">{icon}</div>
                <div style="font-weight:600;color:#e6edf3;margin-bottom:0.4rem;">{name}</div>
                <div style="color:#8b949e;font-size:0.8rem;line-height:1.4;">{desc}</div>
            </div>
            """, unsafe_allow_html=True)
            if st.button(f"Open {name}", key=f"home_{key}", use_container_width=True):
                st.session_state.active_module = key
                st.rerun()

    st.markdown("---")
    st.markdown("### 🚀 Quick Start")
    st.markdown("""
    1. **First time?** Start with 📄 **Resume Analyzer** — paste your resume + any job description
    2. **Know your gaps?** Go to 🗺️ **Learning Roadmap** — paste 3-5 JDs you want to apply for
    3. **Got an interview?** Use 🎤 **Interview Coach** — get 20 role-specific questions instantly
    4. **Applying today?** ✉️ **Cover Letter** writes 3 versions + cold email in 30 seconds
    5. **Daily habit:** 📰 **Daily Briefing** — read your AI market briefing every morning
    """)

    st.markdown("---")

    # Stats from DB
    st.markdown("### 📊 Your Activity")
    try:
        from utils.db import get_conn
        conn = get_conn()
        c = conn.cursor()
        stats = {}
        for table, label in [("resume_analyses","Resume Analyses"), ("interview_sessions","Interview Sessions"),
                             ("cover_letters","Cover Letters"), ("github_analyses","GitHub Analyses"),
                             ("roadmaps","Roadmaps Created"), ("daily_briefings","Daily Briefings")]:
            try:
                c.execute(f"SELECT COUNT(*) FROM {table}")
                stats[label] = c.fetchone()[0]
            except:
                stats[label] = 0
        conn.close()

        stat_cols = st.columns(6)
        for i, (label, count) in enumerate(stats.items()):
            with stat_cols[i]:
                st.metric(label, count)
    except:
        pass

elif module == "resume":
    from modules import resume_analyzer
    resume_analyzer.run()

elif module == "trends":
    from modules import skill_trends
    skill_trends.run()

elif module == "interview":
    from modules import interview_gen
    interview_gen.run()

elif module == "cover":
    from modules import cover_letter
    cover_letter.run()

elif module == "salary":
    from modules import salary_estimator
    salary_estimator.run()

elif module == "briefing":
    from modules import daily_briefing
    daily_briefing.run()

elif module == "github":
    from modules import github_analyzer
    github_analyzer.run()

elif module == "roadmap":
    from modules import roadmap_gen
    roadmap_gen.run()
