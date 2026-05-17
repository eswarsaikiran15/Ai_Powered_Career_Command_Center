import os
import json
import requests
import streamlit as st
import plotly.graph_objects as go
from datetime import datetime
from utils.groq_helper import groq_json
from utils.db import get_conn
from utils.exports import export_pdf


def fetch_github_profile(username: str) -> dict:
    """Fetch GitHub profile data."""
    token = os.getenv("GITHUB_TOKEN", "")
    headers = {"Authorization": f"token {token}"} if token else {}

    try:
        # User profile
        user_res = requests.get(f"https://api.github.com/users/{username}",
                                headers=headers, timeout=10)
        if user_res.status_code == 404:
            return {"error": "User not found"}
        if user_res.status_code == 403:
            return {"error": "Rate limit exceeded. Add GITHUB_TOKEN to .env"}
        user = user_res.json()

        # Repos
        repos_res = requests.get(f"https://api.github.com/users/{username}/repos?per_page=100&sort=updated",
                                  headers=headers, timeout=10)
        repos = repos_res.json() if repos_res.status_code == 200 else []

        # Language stats
        languages = {}
        total_stars = 0
        total_forks = 0
        has_readme = 0

        for repo in repos[:20]:
            lang = repo.get("language")
            if lang:
                languages[lang] = languages.get(lang, 0) + 1
            total_stars += repo.get("stargazers_count", 0)
            total_forks += repo.get("forks_count", 0)
            if repo.get("description"):
                has_readme += 1

        top_repos = sorted(repos, key=lambda r: r.get("stargazers_count", 0), reverse=True)[:5]

        return {
            "username": username,
            "name": user.get("name", username),
            "bio": user.get("bio", ""),
            "location": user.get("location", ""),
            "followers": user.get("followers", 0),
            "following": user.get("following", 0),
            "public_repos": user.get("public_repos", 0),
            "created_at": user.get("created_at", ""),
            "languages": languages,
            "total_stars": total_stars,
            "total_forks": total_forks,
            "repos_with_description": has_readme,
            "top_repos": [{"name": r["name"], "description": r.get("description",""),
                           "stars": r.get("stargazers_count",0), "language": r.get("language",""),
                           "url": r.get("html_url","")} for r in top_repos],
            "avatar_url": user.get("avatar_url", ""),
            "profile_url": f"https://github.com/{username}"
        }
    except Exception as e:
        return {"error": str(e)}


def save_github_analysis(username: str, score: int, result: dict):
    try:
        conn = get_conn()
        c = conn.cursor()
        c.execute("INSERT INTO github_analyses (username, score, full_result) VALUES (?,?,?)",
                  (username, score, json.dumps(result)))
        conn.commit()
        conn.close()
    except:
        pass


def delete_github_analysis(timestamp: str):
    """Delete a specific GitHub analysis from database."""
    try:
        conn = get_conn()
        c = conn.cursor()
        c.execute("DELETE FROM github_analyses WHERE timestamp = ?", (timestamp,))
        conn.commit()
        conn.close()
        return True
    except:
        return False


def run():
    st.markdown("## 🐙 GitHub Profile Analyzer")
    st.caption("AI analyzes your GitHub profile and tells you exactly how to make it recruiter-ready.")

    col1, col2 = st.columns([3, 1])
    with col1:
        username = st.text_input("GitHub Username", placeholder="e.g. torvalds, gvanrossum, your-username")
    with col2:
        target_role = st.text_input("Target Role", placeholder="Data Analyst")

    if st.button("🔍 Analyse Profile", type="primary", use_container_width=True, disabled=not username):
        with st.spinner(f"Fetching @{username}'s GitHub data..."):
            profile = fetch_github_profile(username)

            if profile.get("error"):
                st.error(f"❌ {profile['error']}")
                return

        with st.spinner("Running AI analysis..."):
            lang_summary = ", ".join([f"{k}: {v} repos" for k, v in
                                      sorted(profile["languages"].items(), key=lambda x: -x[1])[:8]])
            top_repos_summary = "\n".join([
                f"- {r['name']} ({r['language'] or 'N/A'}): {r['description'] or 'No description'} | ⭐{r['stars']}"
                for r in profile["top_repos"]
            ])

            prompt = f"""You are a senior tech recruiter analysing a GitHub profile. Return ONLY valid JSON:
{{
  "overall_score": 7,
  "profile_grade": "B+",
  "recruiter_first_impression": "What a recruiter thinks in first 10 seconds",
  "strengths": ["strength1", "strength2", "strength3"],
  "critical_improvements": [
    {{"issue": "No project descriptions", "impact": "High", "fix": "Add 2-3 sentence descriptions to all repos", "effort": "5 minutes"}}
  ],
  "readme_score": 6,
  "readme_feedback": "Your README analysis",
  "project_quality_score": 7,
  "project_diversity_score": 6,
  "activity_score": 5,
  "portfolio_gaps": ["Missing data projects", "No API projects"],
  "suggested_projects": [
    {{"name": "Project name", "description": "What to build", "why": "Why this helps", "tech": ["Python", "SQL"]}}
  ],
  "profile_bio_suggestion": "Suggested bio text",
  "pinned_repos_advice": "Which repos to pin",
  "keywords_to_add": ["keyword1", "keyword2"],
  "career_readiness": "65% recruiter-ready",
  "top_skill": "Your strongest demonstrated skill",
  "missing_for_role": ["skill1 missing for {target_role or 'developer'} role"]
}}

GitHub Profile Data:
Username: {profile['username']}
Name: {profile['name']}
Bio: {profile['bio']}
Followers: {profile['followers']} | Following: {profile['following']}
Public Repos: {profile['public_repos']}
Total Stars: {profile['total_stars']}
Repos with descriptions: {profile['repos_with_description']}/{min(profile['public_repos'],20)}
Languages: {lang_summary}

Top Repositories:
{top_repos_summary}

Target Role: {target_role or 'Software/Data role'}"""

            try:
                result = groq_json(prompt, max_tokens=2000)
                save_github_analysis(username, result.get("overall_score", 0), result)
                _render_analysis(profile, result, username)
            except Exception as e:
                st.error(f"AI analysis failed: {e}")

    # History
    with st.expander("📚 Previous Analyses"):
        try:
            conn = get_conn()
            c = conn.cursor()
            c.execute("SELECT timestamp, username, score FROM github_analyses ORDER BY timestamp DESC LIMIT 10")
            rows = c.fetchall()
            conn.close()
            if rows:
                for idx, (timestamp, username, score) in enumerate(rows):
                    col_text, col_btn = st.columns([4, 1])
                    with col_text:
                        st.markdown(f"**@{username}** — Score: `{score}/10` — {timestamp}")
                    with col_btn:
                        if st.button("🗑️ Delete", key=f"del_github_{idx}", help="Delete this analysis"):
                            if delete_github_analysis(timestamp):
                                st.success("✅ Deleted!")
                                st.rerun()
                            else:
                                st.error("❌ Failed to delete")
            else:
                st.info("No analyses yet.")
        except:
            st.info("No history available.")


def _render_analysis(profile: dict, result: dict, username: str):
    st.markdown("---")

    # Profile header
    col1, col2 = st.columns([1, 3])
    with col1:
        if profile.get("avatar_url"):
            st.image(profile["avatar_url"], width=120)
    with col2:
        score = result.get("overall_score", 0)
        grade = result.get("profile_grade", "")
        color = "#22c55e" if score >= 7 else "#f59e0b" if score >= 5 else "#ef4444"
        st.markdown(f"""
        <h2 style="margin:0;">@{username} <span style="color:{color};">{grade}</span></h2>
        <p style="color:#aaa;">📍 {profile.get('location','')} | ⭐ {profile.get('total_stars',0)} stars | 
        👥 {profile.get('followers',0)} followers | 📁 {profile.get('public_repos',0)} repos</p>
        <p style="color:#87ceeb;">{result.get('recruiter_first_impression','')}</p>
        """, unsafe_allow_html=True)

    st.markdown("---")

    # Score metrics
    m1, m2, m3, m4 = st.columns(4)
    m1.metric("Overall Score", f"{score}/10")
    m2.metric("README Score", f"{result.get('readme_score', 0)}/10")
    m3.metric("Project Quality", f"{result.get('project_quality_score', 0)}/10")
    m4.metric("Activity Score", f"{result.get('activity_score', 0)}/10")

    st.markdown("---")

    # Language chart
    if profile.get("languages"):
        langs = profile["languages"]
        fig = go.Figure(go.Bar(
            x=list(langs.keys()),
            y=list(langs.values()),
            marker_color='#3b82f6'
        ))
        fig.update_layout(
            title="Languages Used Across Repos",
            plot_bgcolor='rgba(0,0,0,0)',
            paper_bgcolor='rgba(0,0,0,0)',
            font=dict(color='white'),
            height=300
        )
        st.plotly_chart(fig, use_container_width=True)

    col_a, col_b = st.columns(2)

    with col_a:
        st.markdown("### 💪 Strengths")
        for s in result.get("strengths", []):
            st.success(f"✅ {s}")

    with col_b:
        st.markdown("### 🔧 Critical Improvements")
        for issue in result.get("critical_improvements", []):
            with st.expander(f"⚠️ {issue.get('issue','')} — Impact: {issue.get('impact','')}"):
                st.markdown(f"**Fix:** {issue.get('fix','')}")
                st.markdown(f"**Effort:** {issue.get('effort','')}")

    st.markdown("---")

    st.markdown("### 🚀 Suggested Projects to Build")
    for proj in result.get("suggested_projects", []):
        with st.expander(f"💡 {proj.get('name','')}"):
            st.markdown(f"**What:** {proj.get('description','')}")
            st.markdown(f"**Why:** {proj.get('why','')}")
            techs = proj.get("tech", [])
            if techs:
                tags = " ".join([f'<span style="background:#1e3a4a;color:#87ceeb;padding:2px 10px;border-radius:12px;margin:2px;display:inline-block;">{t}</span>' for t in techs])
                st.markdown(tags, unsafe_allow_html=True)

    st.markdown("---")

    col_c, col_d = st.columns(2)
    with col_c:
        if result.get("profile_bio_suggestion"):
            st.markdown("### ✏️ Suggested Bio")
            st.info(result["profile_bio_suggestion"])
        if result.get("keywords_to_add"):
            st.markdown("### 🔑 Keywords to Add to Profile")
            for kw in result["keywords_to_add"]:
                st.markdown(f"→ `{kw}`")

    with col_d:
        if result.get("pinned_repos_advice"):
            st.markdown("### 📌 Pinned Repos Advice")
            st.info(result["pinned_repos_advice"])
        if result.get("career_readiness"):
            st.markdown("### 🎯 Career Readiness")
            st.success(f"📊 {result['career_readiness']}")

    st.markdown("---")

    sections = [
        {"heading": f"GitHub Analysis: @{username}", "content": f"Score: {score}/10 | Grade: {grade}"},
        {"heading": "Recruiter First Impression", "content": result.get("recruiter_first_impression","")},
        {"heading": "Strengths", "content": result.get("strengths",[])},
        {"heading": "Critical Improvements", "content": [f"{i.get('issue','')} → Fix: {i.get('fix','')}" for i in result.get("critical_improvements",[])]},
        {"heading": "Suggested Projects", "content": [f"{p.get('name','')} — {p.get('description','')}" for p in result.get("suggested_projects",[])]},
        {"heading": "Profile Bio Suggestion", "content": result.get("profile_bio_suggestion","")},
        {"heading": "Keywords to Add", "content": result.get("keywords_to_add",[])},
    ]

    st.download_button("📥 Download GitHub Analysis PDF",
                       export_pdf(f"GitHub Profile Analysis — @{username}", sections),
                       file_name=f"github_analysis_{username}.pdf",
                       mime="application/pdf",
                       use_container_width=True)
