import json
import requests
import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
from datetime import datetime, timedelta
from utils.groq_helper import groq_json
from utils.db import get_conn


def fetch_hackernews_hiring():
    """Fetch latest Who's Hiring post from HackerNews."""
    try:
        # Get top stories to find Who's Hiring
        res = requests.get("https://hacker-news.firebaseio.com/v0/algolia?tags=ask_hn,hiring",
                           timeout=10)
        # Use search API instead
        search_url = "https://hn.algolia.com/api/v1/search?query=Ask+HN+Who+is+hiring&tags=ask_hn&hitsPerPage=1"
        res = requests.get(search_url, timeout=10)
        data = res.json()
        if data.get("hits"):
            post_id = data["hits"][0]["objectID"]
            # Get comments
            item_res = requests.get(f"https://hacker-news.firebaseio.com/v0/item/{post_id}.json", timeout=10)
            item = item_res.json()
            kids = item.get("kids", [])[:80]  # first 80 comments
            comments = []
            for kid_id in kids[:30]:  # limit to 30 for speed
                try:
                    kid_res = requests.get(f"https://hacker-news.firebaseio.com/v0/item/{kid_id}.json", timeout=5)
                    kid = kid_res.json()
                    if kid and kid.get("text"):
                        comments.append(kid["text"][:500])
                except:
                    continue
            return "\n".join(comments)
    except Exception as e:
        return ""


def get_cached_trends():
    """Get trends from DB if fetched within last 6 hours."""
    try:
        conn = get_conn()
        c = conn.cursor()
        c.execute("SELECT fetched_at, skills_json FROM skill_trends ORDER BY fetched_at DESC LIMIT 1")
        row = c.fetchone()
        conn.close()
        if row:
            fetched_at = datetime.fromisoformat(row[0])
            if datetime.now() - fetched_at < timedelta(hours=6):
                return json.loads(row[1])
    except:
        pass
    return None


def save_trends(skills_data: dict):
    try:
        conn = get_conn()
        c = conn.cursor()
        c.execute("INSERT INTO skill_trends (skills_json) VALUES (?)", (json.dumps(skills_data),))
        conn.commit()
        conn.close()
    except:
        pass


def run():
    st.markdown("## 📈 Live Job Market Skill Trends")
    st.caption("Real-time skill demand pulled from HackerNews 'Who's Hiring' + AI analysis")

    col1, col2 = st.columns([3, 1])
    with col2:
        force_refresh = st.button("🔄 Refresh Now", use_container_width=True)

    cached = get_cached_trends() if not force_refresh else None

    if cached:
        st.info("📦 Showing cached results (updated within last 6 hours). Click Refresh to update.")
        skills_data = cached
    else:
        with st.spinner("Fetching live data from HackerNews and analysing with AI..."):
            raw_text = fetch_hackernews_hiring()

            if not raw_text:
                st.warning("Could not fetch live HackerNews data. Showing AI-generated market analysis instead.")
                raw_text = "Software engineering jobs requiring Python, JavaScript, React, TypeScript, AWS, Docker, Kubernetes, SQL, machine learning, data analysis"

            prompt = f"""Analyse these job posting texts and return ONLY valid JSON with the most in-demand skills:
{{
  "top_skills": [
    {{"skill": "Python", "demand_score": 95, "category": "Programming", "trend": "rising"}},
    {{"skill": "SQL", "demand_score": 88, "category": "Data", "trend": "stable"}},
    {{"skill": "AWS", "demand_score": 82, "category": "Cloud", "trend": "rising"}}
  ],
  "categories": {{
    "Programming": ["Python", "JavaScript"],
    "Data": ["SQL", "Pandas"],
    "Cloud": ["AWS", "GCP"],
    "AI/ML": ["PyTorch", "Scikit-learn"],
    "DevOps": ["Docker", "Kubernetes"],
    "Frameworks": ["React", "FastAPI"]
  }},
  "insights": ["Insight 1", "Insight 2", "Insight 3"],
  "emerging_skills": ["skill1", "skill2", "skill3"],
  "declining_skills": ["skill1"],
  "top_roles": ["Role 1", "Role 2", "Role 3", "Role 4", "Role 5"]
}}

Job posting data:
{raw_text[:3000]}

Return exactly 20 skills in top_skills with realistic demand scores 1-100."""

            try:
                # Try models in order with automatic fallback
                models_to_try = [
                    ("llama-3.3-70b-versatile", 1500),
                    ("openai/gpt-oss-120b", 1500),
                    ("llama-3.1-8b-instant", 1500)
                ]
                
                skills_data = None
                last_error = None
                for model, max_tokens in models_to_try:
                    try:
                        skills_data = groq_json(prompt, model=model, max_tokens=max_tokens)
                        break  # Success, exit loop
                    except Exception as e:
                        error_msg = str(e).lower()
                        last_error = e
                        
                        # Retry with next model on rate limits or JSON errors
                        if "rate_limit" in error_msg or "429" in error_msg or "413" in error_msg or "expecting value" in error_msg or "limit" in error_msg:
                            continue  # Try next model
                        else:
                            raise  # Other errors, don't try next model
                
                if skills_data:
                    save_trends(skills_data)
                else:
                    if last_error:
                        error_str = str(last_error)
                        if "rate_limit" in error_str.lower() or "limit" in error_str.lower():
                            st.error("⏳ **API limit exhausted for today.** All models have reached their daily token limit. Please try again tomorrow!")
                        else:
                            st.error(f"❌ Analysis failed: {error_str[:100]}... Please try again.")
                    else:
                        st.error("❌ All models are currently at capacity. Please try again tomorrow!")
                    return
            except Exception as e:
                error_str = str(e)
                if "rate_limit" in error_str.lower() or "limit" in error_str.lower():
                    st.error("⏳ **API limit exhausted for today.** All models have reached their daily token limit. Please try again tomorrow!")
                else:
                    st.error(f"AI analysis failed: {error_str}")
                return

    # ── Render ────────────────────────────────────────────────────────────────
    top_skills = skills_data.get("top_skills", [])

    if top_skills:
        df = pd.DataFrame(top_skills)
        df = df.sort_values("demand_score", ascending=True).tail(15)

        color_map = {
            "rising": "#22c55e",
            "stable": "#3b82f6",
            "declining": "#ef4444"
        }
        colors = [color_map.get(t, "#3b82f6") for t in df.get("trend", ["stable"] * len(df))]

        fig = go.Figure(go.Bar(
            x=df["demand_score"],
            y=df["skill"],
            orientation='h',
            marker_color=colors,
            text=df["demand_score"].astype(str) + "%",
            textposition='outside'
        ))
        fig.update_layout(
            title="Top Skills in Demand Right Now",
            plot_bgcolor='rgba(0,0,0,0)',
            paper_bgcolor='rgba(0,0,0,0)',
            font=dict(color='white'),
            xaxis=dict(range=[0, 110], showgrid=False),
            yaxis=dict(showgrid=False),
            height=500,
            margin=dict(l=20, r=60, t=50, b=20)
        )
        st.plotly_chart(fig, use_container_width=True)

    st.markdown("---")

    # Categories
    categories = skills_data.get("categories", {})
    if categories:
        st.markdown("### 🗂️ Skills by Category")
        cols = st.columns(3)
        for i, (cat, skills) in enumerate(categories.items()):
            with cols[i % 3]:
                st.markdown(f"**{cat}**")
                for skill in skills:
                    st.markdown(f'<span style="background:#1e3a4a;color:#87ceeb;padding:2px 10px;border-radius:12px;margin:2px;display:inline-block;font-size:0.8rem;">{skill}</span>',
                                unsafe_allow_html=True)
                st.markdown("")

    st.markdown("---")
    col_a, col_b = st.columns(2)

    with col_a:
        emerging = skills_data.get("emerging_skills", [])
        if emerging:
            st.markdown("### 🚀 Emerging Skills to Learn Now")
            for skill in emerging:
                st.success(f"⬆️ {skill}")

    with col_b:
        declining = skills_data.get("declining_skills", [])
        if declining:
            st.markdown("### 📉 Declining Skills")
            for skill in declining:
                st.warning(f"⬇️ {skill}")

    st.markdown("---")
    insights = skills_data.get("insights", [])
    if insights:
        st.markdown("### 💡 Market Insights")
        for insight in insights:
            st.info(f"📊 {insight}")

    top_roles = skills_data.get("top_roles", [])
    if top_roles:
        st.markdown("### 💼 Most Hired Roles Right Now")
        cols = st.columns(len(top_roles[:5]))
        for i, role in enumerate(top_roles[:5]):
            with cols[i]:
                st.markdown(f'<div style="background:#1e3a4a;border-radius:8px;padding:1rem;text-align:center;color:#87ceeb;font-weight:600;">{role}</div>',
                            unsafe_allow_html=True)
