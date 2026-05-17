import os
import json
import requests
import streamlit as st
from datetime import datetime, date
from utils.groq_helper import groq_text
from utils.db import get_conn
from utils.exports import export_pdf


def fetch_tech_news(api_key: str) -> list:
    """Fetch tech news from NewsAPI."""
    if not api_key:
        return []
    try:
        url = f"https://newsapi.org/v2/top-headlines?category=technology&pageSize=10&apiKey={api_key}"
        res = requests.get(url, timeout=8)
        return res.json().get("articles", [])
    except:
        return []


def fetch_hn_top() -> list:
    """Fetch top HackerNews stories."""
    try:
        ids_res = requests.get("https://hacker-news.firebaseio.com/v0/topstories.json", timeout=8)
        ids = ids_res.json()[:10]
        stories = []
        for sid in ids[:8]:
            try:
                s = requests.get(f"https://hacker-news.firebaseio.com/v0/item/{sid}.json", timeout=5).json()
                if s and s.get("title"):
                    stories.append({"title": s.get("title", ""), "score": s.get("score", 0),
                                    "url": s.get("url", "")})
            except:
                continue
        return stories
    except:
        return []


def get_today_briefing() -> str:
    """Get today's briefing from DB if already generated."""
    try:
        conn = get_conn()
        c = conn.cursor()
        today = date.today().isoformat()
        c.execute("SELECT briefing FROM daily_briefings WHERE date = ?", (today,))
        row = c.fetchone()
        conn.close()
        return row[0] if row else None
    except:
        return None


def save_briefing(briefing: str):
    try:
        conn = get_conn()
        c = conn.cursor()
        today = date.today().isoformat()
        c.execute("INSERT OR REPLACE INTO daily_briefings (date, briefing) VALUES (?,?)",
                  (today, briefing))
        conn.commit()
        conn.close()
    except:
        pass


def delete_briefing(date_str: str):
    """Delete a specific briefing from database."""
    try:
        conn = get_conn()
        c = conn.cursor()
        c.execute("DELETE FROM daily_briefings WHERE date = ?", (date_str,))
        conn.commit()
        conn.close()
        return True
    except:
        return False


def send_to_telegram(message: str, bot_token: str, chat_id: str) -> bool:
    """Send message to Telegram."""
    try:
        url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
        res = requests.post(url, json={
            "chat_id": chat_id,
            "text": message[:4096],
            "parse_mode": "Markdown"
        }, timeout=10)
        return res.status_code == 200
    except:
        return False


def run():
    st.markdown("## 📰 Daily Job Market Briefing")
    st.caption("Your personalized AI-written tech and job market briefing — fresh every day.")

    col1, col2 = st.columns([3, 1])
    with col2:
        force_refresh = st.button("🔄 Generate Fresh", use_container_width=True)

    today_briefing = get_today_briefing() if not force_refresh else None

    if today_briefing:
        st.success("✅ Today's briefing is ready!")
        _render_briefing(today_briefing)
    else:
        with st.spinner("Fetching live tech news and writing your briefing..."):
            news_api_key = os.getenv("NEWS_API_KEY", "")
            articles = fetch_tech_news(news_api_key)
            hn_stories = fetch_hn_top()

            news_context = ""
            if articles:
                news_context += "**Tech News Headlines:**\n"
                for a in articles[:6]:
                    news_context += f"- {a.get('title','')}: {a.get('description','')}\n"

            if hn_stories:
                news_context += "\n**Top HackerNews Stories:**\n"
                for s in hn_stories[:6]:
                    news_context += f"- {s['title']} (Score: {s['score']})\n"

            if not news_context:
                news_context = "General tech industry trends for today."

            prompt = f"""You are a professional tech career journalist. Write a daily briefing newsletter for job seekers in the tech industry.

Today's Date: {datetime.now().strftime('%B %d, %Y')}

Available News Data:
{news_context}

Write a comprehensive briefing in this EXACT format:

# 🌅 Tech Career Daily Briefing — {datetime.now().strftime('%B %d, %Y')}

## 📊 Market Pulse
[2-3 sentences about overall tech job market today]

## 🔥 Today's Top Tech Stories
[3-4 bullet points summarizing key tech news relevant to job seekers]

## 💼 Hiring Trends
[2-3 sentences about what companies are hiring for right now]

## 🛠️ Skill of the Day
[One skill to learn today with brief explanation of why it matters]

## 💡 Career Tip of the Day
[One actionable career tip]

## 📈 Opportunities to Watch
[2-3 industries or roles seeing increased hiring]

## 🎯 Today's Action Item
[One specific thing a job seeker should do today]

Keep it concise, motivating, and practical. Write for freshers and early-career professionals."""

            try:
                briefing = groq_text(prompt, max_tokens=1500)
                save_briefing(briefing)
                _render_briefing(briefing)
            except Exception as e:
                st.error(f"Could not generate briefing: {e}")
                return

    st.markdown("---")
    # Telegram send
    with st.expander("📱 Send to Telegram"):
        st.markdown("""
        **Our Official Bot:** [@careercommandcenterbot](https://t.me/careercommandcenterbot)
        
        Or create your own bot:
        """)
        
        bot_token = os.getenv("TELEGRAM_BOT_TOKEN", "")
        chat_id = os.getenv("TELEGRAM_CHAT_ID", "")
        
        if bot_token and chat_id:
            st.success("✅ Telegram credentials loaded from `.env`")
            if st.button("📤 Send Briefing to Telegram"):
                if today_briefing:
                    success = send_to_telegram(today_briefing, bot_token, chat_id)
                    if success:
                        st.success("✅ Sent to Telegram!")
                    else:
                        st.error("❌ Failed. Check your bot token and chat ID in `.env`")
                else:
                    st.warning("Generate a briefing first.")
        else:
            st.warning("⚠️ Telegram not configured in `.env`")
            st.markdown("""
            **Setup Instructions:**
            
            **Option 1: Use Our Bot**
            - Start using [@careercommandcenterbot](https://t.me/careercommandcenterbot) directly
            
            **Option 2: Create Your Own Bot**
            1. Message [@BotFather](https://t.me/botfather) → `/newbot`
            2. Enter bot name: `careercommandcenterbot` (or your preferred name)
            3. Copy the token BotFather provides
            4. Message [@userinfobot](https://t.me/userinfobot) to get your Chat ID
            5. Save both to `.env`:
            ```
            TELEGRAM_BOT_TOKEN=your_token_here
            TELEGRAM_CHAT_ID=your_chat_id_here
            ```
            6. Restart the app
            """)

    # History
    with st.expander("📚 Past Briefings"):
        try:
            conn = get_conn()
            c = conn.cursor()
            c.execute("SELECT date, briefing FROM daily_briefings ORDER BY date DESC LIMIT 7")
            rows = c.fetchall()
            conn.close()
            if rows:
                for idx, (date_str, briefing) in enumerate(rows):
                    col_date, col_del = st.columns([4, 1])
                    with col_date:
                        with st.expander(f"📅 {date_str}"):
                            st.markdown(briefing)
                    with col_del:
                        if st.button("🗑️", key=f"del_brief_{idx}", help="Delete this briefing"):
                            if delete_briefing(date_str):
                                st.success("✅ Deleted!")
                                st.rerun()
                            else:
                                st.error("❌ Failed to delete")
            else:
                st.info("No briefings yet.")
        except:
            st.info("No history available.")


def _render_briefing(briefing: str):
    st.markdown(briefing)

    st.markdown("---")
    pdf_bytes = export_pdf(
        f"Daily Briefing — {datetime.now().strftime('%B %d, %Y')}",
        [{"heading": "Today's Briefing", "content": briefing}]
    )
    st.download_button("📥 Download Briefing as PDF", pdf_bytes,
                       file_name=f"briefing_{date.today().isoformat()}.pdf",
                       mime="application/pdf")
