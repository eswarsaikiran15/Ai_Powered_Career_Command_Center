import json
import requests
import streamlit as st
import plotly.graph_objects as go
from datetime import datetime
from utils.groq_helper import groq_json
from utils.db import get_conn
from utils.exports import export_pdf, export_docx


def fetch_wikipedia_summary(skill: str) -> str:
    """Fetch a brief Wikipedia summary for a skill."""
    try:
        res = requests.get(
            f"https://en.wikipedia.org/api/rest_v1/page/summary/{skill.replace(' ','_')}",
            timeout=5)
        if res.status_code == 200:
            return res.json().get("extract", "")[:200]
    except:
        pass
    return ""


def save_roadmap(roles: str, roadmap: dict):
    try:
        conn = get_conn()
        c = conn.cursor()
        c.execute("INSERT INTO roadmaps (target_roles, roadmap_json) VALUES (?,?)",
                  (roles, json.dumps(roadmap)))
        conn.commit()
        conn.close()
        return c.lastrowid
    except:
        return None


def get_roadmap_by_id(roadmap_id: int) -> dict:
    try:
        conn = get_conn()
        c = conn.cursor()
        c.execute("SELECT roadmap_json, completed_skills FROM roadmaps WHERE id=?", (roadmap_id,))
        row = c.fetchone()
        conn.close()
        if row:
            return {"roadmap": json.loads(row[0]), "completed": json.loads(row[1])}
    except:
        pass
    return {}

def delete_roadmap(roadmap_id: int):
    """Delete a specific roadmap from database."""
    try:
        conn = get_conn()
        c = conn.cursor()
        c.execute("DELETE FROM roadmaps WHERE id = ?", (roadmap_id,))
        conn.commit()
        conn.close()
        return True
    except:
        return False

def update_completed(roadmap_id: int, completed: list):
    try:
        conn = get_conn()
        c = conn.cursor()
        c.execute("UPDATE roadmaps SET completed_skills=? WHERE id=?",
                  (json.dumps(completed), roadmap_id))
        conn.commit()
        conn.close()
    except:
        pass


def run():
    st.markdown("## 🗺️ Learning Roadmap Generator")
    st.caption("Paste up to 5 job descriptions. AI extracts required skills, compares to your resume, and builds a week-by-week learning plan.")

    resume_text = st.text_area("📄 Your Current Resume / Skills",
                                height=150, placeholder="Paste your resume or list your current skills...")

    st.markdown("### 📋 Paste Job Descriptions You Want to Apply For")
    jd_tabs = st.tabs([f"JD {i+1}" for i in range(5)])
    jds = []
    for i, tab in enumerate(jd_tabs):
        with tab:
            jd = st.text_area(f"Job Description {i+1}", height=180, key=f"jd_{i}",
                               label_visibility="collapsed",
                               placeholder=f"Paste job description {i+1} here (optional)...")
            if jd.strip():
                jds.append(jd)

    experience_level = st.selectbox("Your Current Level",
                                     ["Complete Beginner", "Some Knowledge", "Intermediate", "Advanced"])
    hours_per_week = st.slider("Hours available to learn per week", 5, 40, 15)
    learning_style = st.multiselect("Learning Preferences",
                                     ["Video Courses", "Books/Documentation", "Projects", "Practice Problems", "Mentorship"],
                                     default=["Video Courses", "Projects"])

    if st.button("🗺️ Generate My Roadmap", type="primary", use_container_width=True,
                 disabled=not (resume_text and jds)):
        with st.spinner("Analysing job requirements and building your personalized roadmap..."):

            combined_jds = "\n\n---\n\n".join(jds[:5])

            prompt = f"""You are a career coach and curriculum designer. Analyse these job descriptions and create a personalized learning roadmap. Return ONLY valid JSON:
{{
  "target_roles": ["Role 1", "Role 2"],
  "current_skills": ["skill1", "skill2"],
  "required_skills": ["skill1", "skill2", "skill3"],
  "skill_gaps": [
    {{
      "skill": "Python",
      "priority": "High",
      "reason": "Required in 3/4 JDs",
      "estimated_weeks": 3,
      "free_resources": ["resource1", "resource2"],
      "practice_project": "Build a data pipeline"
    }}
  ],
  "weekly_plan": [
    {{
      "week": 1,
      "theme": "Python Fundamentals",
      "skills": ["Variables", "Functions", "Loops"],
      "daily_tasks": ["Day 1: Install Python + basics", "Day 2: Functions practice"],
      "project": "Build a simple calculator",
      "hours_needed": 15,
      "milestone": "Complete Python basics"
    }}
  ],
  "total_weeks": 12,
  "quick_wins": ["skill you can learn in 1 day"],
  "certifications_path": [
    {{"name": "Google Data Analytics", "platform": "Coursera", "free": true, "weeks": 6}}
  ],
  "monthly_milestones": ["Month 1: Complete Python", "Month 2: SQL mastery"],
  "job_ready_date": "Estimated date to be job-ready",
  "motivation_message": "Personalized encouragement message"
}}

Resume/Current Skills:
{resume_text[:2000]}

Job Descriptions:
{combined_jds[:3000]}

Experience Level: {experience_level}
Hours per week available: {hours_per_week}
Learning preferences: {', '.join(learning_style)}

Create a realistic {max(8, hours_per_week)}+ week roadmap. Be specific with free resources."""

            try:
                roadmap = groq_json(prompt, max_tokens=3000)
                roadmap_id = save_roadmap(", ".join(roadmap.get("target_roles",[])), roadmap)
                if "current_roadmap_id" not in st.session_state:
                    st.session_state.current_roadmap_id = roadmap_id
                st.session_state.current_roadmap = roadmap
                _render_roadmap(roadmap, roadmap_id)
            except Exception as e:
                st.error(f"Roadmap generation failed: {e}")

    # Show existing roadmap if in session
    elif "current_roadmap" in st.session_state:
        st.info("📌 Showing your last generated roadmap. Generate a new one above.")
        _render_roadmap(st.session_state.current_roadmap,
                        st.session_state.get("current_roadmap_id"))

    # History
    with st.expander("📚 Saved Roadmaps"):
        try:
            conn = get_conn()
            c = conn.cursor()
            c.execute("SELECT id, timestamp, target_roles FROM roadmaps ORDER BY timestamp DESC LIMIT 10")
            rows = c.fetchall()
            conn.close()
            if rows:
                for idx, (roadmap_id, timestamp, target_roles) in enumerate(rows):
                    col_road, col_del = st.columns([4, 1])
                    with col_road:
                        if st.button(f"📋 {target_roles} — {timestamp}", key=f"load_roadmap_{roadmap_id}"):
                            data = get_roadmap_by_id(roadmap_id)
                            if data:
                                st.session_state.current_roadmap = data["roadmap"]
                                st.session_state.current_roadmap_id = roadmap_id
                                st.rerun()
                    with col_del:
                        if st.button("🗑️", key=f"del_road_{idx}", help="Delete this roadmap"):
                            if delete_roadmap(roadmap_id):
                                st.success("✅ Deleted!")
                                st.rerun()
                            else:
                                st.error("❌ Failed to delete")
            else:
                st.info("No saved roadmaps yet.")
        except:
            st.info("No history available.")


def _render_roadmap(roadmap: dict, roadmap_id=None):
    st.markdown("---")

    # Motivation message
    if roadmap.get("motivation_message"):
        st.success(f"💪 {roadmap['motivation_message']}")

    # Key stats
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Total Weeks", roadmap.get("total_weeks", "?"))
    col2.metric("Skill Gaps", len(roadmap.get("skill_gaps", [])))
    col3.metric("Job Ready", roadmap.get("job_ready_date", "TBD"))
    col4.metric("Target Roles", len(roadmap.get("target_roles", [])))

    st.markdown("---")

    # Skill gap priority chart
    gaps = roadmap.get("skill_gaps", [])
    if gaps:
        priority_map = {"High": 3, "Medium": 2, "Low": 1}
        df_skills = sorted(gaps, key=lambda x: priority_map.get(x.get("priority","Low"), 1), reverse=True)

        fig = go.Figure(go.Bar(
            x=[g["skill"] for g in df_skills[:12]],
            y=[g.get("estimated_weeks", 1) for g in df_skills[:12]],
            marker_color=["#ef4444" if g.get("priority")=="High" else
                          "#f59e0b" if g.get("priority")=="Medium" else "#22c55e"
                          for g in df_skills[:12]],
            text=[f"{g.get('priority','')}" for g in df_skills[:12]],
            textposition='outside'
        ))
        fig.update_layout(
            title="Skills to Learn (Red=High Priority, Yellow=Medium, Green=Low)",
            plot_bgcolor='rgba(0,0,0,0)',
            paper_bgcolor='rgba(0,0,0,0)',
            font=dict(color='white'),
            yaxis_title="Weeks to Learn",
            height=350
        )
        st.plotly_chart(fig, use_container_width=True)

    # Skill gaps detail
    st.markdown("### 🎯 Your Skill Gaps (Prioritized)")
    for gap in gaps:
        priority_color = {"High": "#ef4444", "Medium": "#f59e0b", "Low": "#22c55e"}.get(gap.get("priority","Low"), "#aaa")
        with st.expander(f"{'🔴' if gap.get('priority')=='High' else '🟡' if gap.get('priority')=='Medium' else '🟢'} {gap.get('skill','')} — {gap.get('estimated_weeks',1)} weeks"):
            st.markdown(f"**Why it matters:** {gap.get('reason','')}")
            st.markdown(f"**Practice Project:** {gap.get('practice_project','')}")
            resources = gap.get("free_resources", [])
            if resources:
                st.markdown("**Free Resources:**")
                for r in resources:
                    st.markdown(f"→ {r}")

    st.markdown("---")
    st.markdown("### 📅 Week-by-Week Plan")

    # Progress tracking
    if "roadmap_progress" not in st.session_state:
        st.session_state.roadmap_progress = {}

    weekly_plan = roadmap.get("weekly_plan", [])
    total_weeks = len(weekly_plan)
    completed_weeks = sum(1 for w in weekly_plan
                          if st.session_state.roadmap_progress.get(f"week_{w.get('week',0)}", False))

    if total_weeks > 0:
        progress_pct = completed_weeks / total_weeks
        st.progress(progress_pct)
        st.caption(f"Progress: {completed_weeks}/{total_weeks} weeks completed ({int(progress_pct*100)}%)")

    for week in weekly_plan:
        week_num = week.get("week", 0)
        is_done = st.session_state.roadmap_progress.get(f"week_{week_num}", False)
        icon = "✅" if is_done else "📅"

        with st.expander(f"{icon} Week {week_num}: {week.get('theme','')} ({week.get('hours_needed',0)} hrs)"):
            col_l, col_r = st.columns([3, 1])
            with col_l:
                skills = week.get("skills", [])
                if skills:
                    st.markdown(f"**Skills:** {', '.join(skills)}")

                daily = week.get("daily_tasks", [])
                if daily:
                    st.markdown("**Daily Tasks:**")
                    for task in daily:
                        st.markdown(f"→ {task}")

                if week.get("project"):
                    st.info(f"🏗️ **Project:** {week['project']}")
                if week.get("milestone"):
                    st.success(f"🏆 **Milestone:** {week['milestone']}")

            with col_r:
                done = st.checkbox("Mark Complete", value=is_done, key=f"week_check_{week_num}")
                st.session_state.roadmap_progress[f"week_{week_num}"] = done

    st.markdown("---")

    # Monthly milestones
    milestones = roadmap.get("monthly_milestones", [])
    if milestones:
        st.markdown("### 🏆 Monthly Milestones")
        for i, m in enumerate(milestones, 1):
            st.markdown(f"**Month {i}:** {m}")

    # Certifications
    certs = roadmap.get("certifications_path", [])
    if certs:
        st.markdown("### 📜 Certification Path")
        for cert in certs:
            free_badge = "🆓 Free" if cert.get("free") else "💰 Paid"
            st.markdown(f"→ **{cert.get('name','')}** on {cert.get('platform','')} | {free_badge} | {cert.get('weeks',0)} weeks")

    # Quick wins
    quick_wins = roadmap.get("quick_wins", [])
    if quick_wins:
        st.markdown("### ⚡ Quick Wins (Learn Today)")
        for win in quick_wins:
            st.success(f"✨ {win}")

    st.markdown("---")

    # Export
    sections = [
        {"heading": "Target Roles", "content": roadmap.get("target_roles",[])},
        {"heading": "Skill Gaps", "content": [f"{g.get('skill','')} ({g.get('priority','')} priority, {g.get('estimated_weeks',1)} weeks)" for g in gaps]},
        {"heading": "Weekly Plan Summary", "content": [f"Week {w.get('week',0)}: {w.get('theme','')} — {w.get('milestone','')}" for w in weekly_plan]},
        {"heading": "Monthly Milestones", "content": milestones},
        {"heading": "Certifications", "content": [f"{c.get('name','')} — {c.get('platform','')} ({'Free' if c.get('free') else 'Paid'})" for c in certs]},
        {"heading": "Quick Wins", "content": quick_wins},
        {"heading": "Job Ready Date", "content": roadmap.get("job_ready_date","")},
    ]

    c1, c2 = st.columns(2)
    with c1:
        st.download_button("📄 Download Roadmap DOCX",
                           export_docx("My Learning Roadmap", sections),
                           file_name="learning_roadmap.docx",
                           mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                           use_container_width=True)
    with c2:
        st.download_button("📥 Download Roadmap PDF",
                           export_pdf("My Learning Roadmap", sections),
                           file_name="learning_roadmap.pdf",
                           mime="application/pdf",
                           use_container_width=True)
