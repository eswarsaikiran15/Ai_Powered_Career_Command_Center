# 🚀 AI Career Command Center

> Your complete AI-powered job search operating system — 8 tools, zero cost, built with Python + Streamlit + Groq.

![Python](https://img.shields.io/badge/Python-3.9+-blue) ![Streamlit](https://img.shields.io/badge/Streamlit-1.32-red) ![Groq](https://img.shields.io/badge/Groq-Free-green) ![Cost](https://img.shields.io/badge/Cost-₹0-brightgreen)

---

## 🛠️ 8 Powerful Tools Inside

| Tool | What It Does |
|------|-------------|
| 📄 **Resume Analyzer** | Match score, skill gaps, ATS check, rewrite tips, interview questions |
| 📈 **Skill Trends** | Live job market demand from HackerNews + AI analysis |
| 🎤 **Interview Coach** | Role-specific questions with STAR method + answer frameworks |
| ✉️ **Cover Letter Writer** | 3 versions + cold email + LinkedIn message + follow-up |
| 💰 **Salary Estimator** | Compare salaries across countries with real World Bank data |
| 📰 **Daily Briefing** | AI-written daily tech career newsletter + Telegram delivery |
| 🐙 **GitHub Analyzer** | Profile score, improvement tips, project suggestions |
| 🗺️ **Learning Roadmap** | Week-by-week plan built from your target JDs + progress tracking |

---

## ⚡ Quick Setup (5 minutes)

### 1. Clone and install

```bash
git clone https://github.com/yourusername/career_command_center
cd career_command_center
pip install -r requirements.txt
```

### 2. Configure API keys

```bash
cp .env.example .env
```

Edit `.env`:
```
GROQ_API_KEY=gsk_...        # Required — free at console.groq.com
NEWS_API_KEY=...             # Optional — free at newsapi.org
TELEGRAM_BOT_TOKEN=...       # Optional — from @BotFather on Telegram
TELEGRAM_CHAT_ID=...         # Optional — from @userinfobot on Telegram
GITHUB_TOKEN=...             # Optional — increases rate limit
```

### 3. Run

```bash
streamlit run app.py
```

Open: http://localhost:8501

---

## 🔑 Getting Free API Keys

| API | Where to Get | Limit |
|-----|-------------|-------|
| **Groq** (Required) | [console.groq.com](https://console.groq.com) | ~14,400 req/day FREE |
| **NewsAPI** (Optional) | [newsapi.org](https://newsapi.org) | 100 req/day FREE |
| **Telegram Bot** (Optional) | [@BotFather](https://t.me/botfather) | Unlimited FREE |
| **GitHub Token** (Optional) | [github.com/settings/tokens](https://github.com/settings/tokens) | 5000 req/hr FREE |

---

## 📁 Project Structure

```
career_command_center/
├── app.py                    # Main Streamlit app + navigation
├── modules/
│   ├── resume_analyzer.py    # Module 1: Resume analysis
│   ├── skill_trends.py       # Module 2: HackerNews skill trends
│   ├── interview_gen.py      # Module 3: Interview questions
│   ├── cover_letter.py       # Module 4: Cover letter writer
│   ├── salary_estimator.py   # Module 5: Salary comparison
│   ├── daily_briefing.py     # Module 6: Daily briefing + Telegram
│   ├── github_analyzer.py    # Module 7: GitHub profile analysis
│   └── roadmap_gen.py        # Module 8: Learning roadmap
├── utils/
│   ├── db.py                 # SQLite database setup
│   ├── groq_helper.py        # Groq API wrapper with retry logic
│   └── exports.py            # PDF + DOCX export utilities
├── database/                 # SQLite DB (auto-created)
├── exports/                  # Generated files
├── requirements.txt
├── .env.example
├── .gitignore
└── README.md
```

---

## ⚙️ API Resilience & Failover

All modules include **automatic failover** to handle API rate limits gracefully:

✅ **Multi-Model Fallback Chain**
- Tries `llama-3.3-70b-versatile` (primary)
- Falls back to `openai/gpt-oss-120b` (secondary)
- Falls back to `llama-3.1-8b-instant` (tertiary)
- No manual intervention needed

✅ **Smart Error Handling**
- Detects rate limits (429, 413 errors)
- Detects JSON parse errors
- Detects daily quota exhaustion
- Automatically retries with next model

✅ **User-Friendly Messages**
- No technical jargon shown to users
- Clear "API limit exhausted for today. Please try again tomorrow!" message
- Invisible resilience — users don't see model selection

**Applied across all 8 modules** — Resume Analyzer, Skill Trends, Interview Coach, Cover Letter, Salary Estimator, Daily Briefing, GitHub Analyzer, and Learning Roadmap.

---

## 🌐 Free APIs Used

- **Groq API** — AI brain (Llama 3.3 70b, GPT-OSS 120b, Llama 3.1 8b)
- **HackerNews API** — Live job market data
- **NewsAPI** — Tech news for briefing + cover letters
- **GitHub API** — Profile analysis
- **World Bank API** — GDP data for salary estimates
- **RestCountries API** — Country economic info
- **Frankfurter API** — Currency conversion
- **Wikipedia API** — Skill descriptions for roadmap
- **Telegram Bot API** — Briefing delivery
- **Open-Meteo** — Weather (bonus feature)

**Total cost: ₹0**

---

## 🚀 Deploy for Free

### Streamlit Cloud (Recommended)
1. Push to GitHub
2. Go to [share.streamlit.io](https://share.streamlit.io)
3. Connect your repo
4. Add secrets in Settings → Secrets (same as .env format)
5. Deploy!

---

## 🛡️ Security

- API keys stored in `.env` (never in code)
- `.env` is in `.gitignore` — never committed
- SQLite database is local only
- No user data sent to third parties (only to Groq for AI processing)

---

## 📊 Tech Stack

```
Python 3.9+    Streamlit 1.32    Groq API (Llama 3.3 70b)
SQLite         python-docx       reportlab (PDF)
Plotly         PyPDF2            requests
python-dotenv  schedule
```

---

## 🤝 Contributing

PRs welcome! See open issues.

---

## 📝 License

MIT License — free to use, modify, and distribute.

---

*Built with ❤️ by Kamparapu Eswar Sai Kiran*
