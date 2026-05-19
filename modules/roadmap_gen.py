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
    st.caption("Paste up to 5 job descriptions. AI extracts required skills, compares to your resume, and builds a complete project-based learning plan.")

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

            prompt = f"""You are a curriculum architect designing a complete project-based learning path. Create a DETAILED, PRODUCTION-READY learning plan to build real applications. Return ONLY valid JSON:
{{
  "target_roles": ["Role 1", "Role 2"],
  "current_skills": ["skill1", "skill2"],
  "required_skills": ["skill1", "skill2", "skill3"],
  "tech_stack": {{
    "frontend": ["React", "TypeScript", "Tailwind CSS"],
    "backend": ["Python/Node.js", "FastAPI/Express"],
    "database": ["PostgreSQL", "Redis"],
    "devops": ["Docker", "CI/CD", "AWS/Azure"],
    "tools": ["Git", "Postman", "GitHub"]
  }},
  "skill_gaps": [
    {{
      "skill": "Python",
      "priority": "High",
      "reason": "Required in 3/4 JDs, core backend language",
      "estimated_weeks": 3,
      "free_resources": ["resource1", "resource2"],
      "paid_resources": ["Udemy course"],
      "practice_project": "Build a data pipeline with Flask",
      "hands_on_goal": "Create API with authentication"
    }}
  ],
  "project_development_phases": [
    {{
      "phase": "Phase 1: Foundation (Weeks 1-4)",
      "focus": "Core programming skills & environment setup",
      "project_component": "Setup development environment, version control, basic project structure",
      "deliverables": ["Deployed Hello World app", "GitHub repo", "CI/CD pipeline basics"],
      "tech_focus": ["Environment setup", "Git workflow", "Docker basics"]
    }},
    {{
      "phase": "Phase 2: MVP Backend (Weeks 5-10)",
      "focus": "Build core API and database",
      "project_component": "RESTful API with user authentication",
      "deliverables": ["User auth system", "Database schema", "API documentation"],
      "tech_focus": ["Database design", "Authentication", "API design patterns"]
    }},
    {{
      "phase": "Phase 3: Frontend & Integration (Weeks 11-14)",
      "focus": "Build user interface",
      "project_component": "React components connected to API",
      "deliverables": ["Working UI", "Client-side validation", "Error handling"],
      "tech_focus": ["React patterns", "State management", "API integration"]
    }},
    {{
      "phase": "Phase 4: Scale & Deploy (Weeks 15-20)",
      "focus": "Production readiness",
      "project_component": "Optimization, monitoring, deployment",
      "deliverables": ["Live application", "Monitoring setup", "Documentation"],
      "tech_focus": ["Performance optimization", "DevOps", "Cloud deployment"]
    }}
  ],
  "weekly_plan": [
    {{
      "week": 1,
      "phase": "Foundation",
      "theme": "Python Fundamentals & Setup",
      "skills": ["Variables", "Functions", "Loops", "Git basics"],
      "daily_tasks": [
        "Day 1: Install Python, VS Code, Git. Learn basics",
        "Day 2: Variables, data types, string operations",
        "Day 3: Functions, parameters, return values",
        "Day 4: Loops, conditionals, practice exercises",
        "Day 5: Git workflow, GitHub setup, first commit"
      ],
      "project": "Build a CLI calculator app with functions",
      "project_details": "Create calculator with add, subtract, multiply, divide functions. Save to GitHub.",
      "learning_resources": [
        {{"type": "Video", "name": "Python for Beginners", "platform": "YouTube", "time": "2 hours"}},
        {{"type": "Documentation", "name": "Python Official Docs", "platform": "python.org", "time": "1 hour"}},
        {{"type": "Practice", "name": "Codecademy Python", "platform": "codecademy.com", "time": "2 hours"}}
      ],
      "hours_needed": 15,
      "milestone": "Complete Python basics and first GitHub commit",
      "difficulty": "Easy",
      "checkpoint": "Can write functions and understand loops"
    }}
  ],
  "hands_on_projects": [
    {{
      "name": "Task Management SaaS (Full Stack)",
      "description": "Build a complete task management application",
      "modules": ["User Auth", "Task CRUD", "Real-time updates", "Analytics dashboard"],
      "tech_stack": ["React", "Python/FastAPI", "PostgreSQL", "WebSockets"],
      "estimated_weeks": 8,
      "learning_outcomes": ["Full-stack development", "Database design", "API architecture"],
      "phases": ["Week 1-2: Backend auth", "Week 3-4: Task API", "Week 5-6: Frontend", "Week 7-8: Deployment"]
    }}
  ],
  "learning_path_options": [
    {{
      "path": "Full Stack Engineer Track",
      "duration": "20 weeks",
      "focus": "Building complete applications",
      "weekly_commitment": "20 hours",
      "best_for": "People wanting to build and deploy products"
    }},
    {{
      "path": "Backend Engineer Track",
      "duration": "16 weeks",
      "focus": "APIs, databases, architecture",
      "weekly_commitment": "18 hours",
      "best_for": "People interested in system design"
    }},
    {{
      "path": "Data Engineer Track",
      "duration": "18 weeks",
      "focus": "Data pipelines, analytics, SQL",
      "weekly_commitment": "20 hours",
      "best_for": "Data-focused roles"
    }}
  ],
  "daily_structure": {{
    "morning": "30 min concept review + 1 hour theory",
    "midday": "1.5 hours hands-on coding practice",
    "afternoon": "1 hour project work + 30 min debugging",
    "evening": "30 min documentation reading + reflections"
  }},
  "monthly_milestones": [
    "Month 1: Master core programming + Git workflow",
    "Month 2: Build and deploy simple API",
    "Month 3: Build full-stack mini project",
    "Month 4+: Advanced topics and job-ready projects"
  ],
  "certifications_path": [
    {{"name": "AWS Solutions Architect Associate", "platform": "AWS", "free": false, "weeks": 6, "cost": "$150"}},
    {{"name": "Google Data Analytics Certificate", "platform": "Coursera", "free": false, "weeks": 6, "cost": "$39"}},
    {{"name": "Docker & Kubernetes Fundamentals", "platform": "Linux Academy", "free": false, "weeks": 4, "cost": "$99"}}
  ],
  "quick_wins": [
    "Learn Python lists & dictionaries (1 day - high impact)",
    "Deploy app to Heroku (1 day - confidence builder)",
    "Write first SQL query (1 day - database understanding)",
    "Create first REST API endpoint (2 days - core skill)"
  ],
  "interview_prep_schedule": [
    {{"week": 16, "focus": "System design basics", "time": "3 hours"}},
    {{"week": 17, "focus": "Coding interview practice", "time": "3 hours"}},
    {{"week": 18, "focus": "Behavioral interview prep", "time": "2 hours"}},
    {{"week": 19, "focus": "Mock interviews", "time": "4 hours"}},
    {{"week": 20, "focus": "Resume optimization", "time": "2 hours"}}
  ],
  "technical_debt_checklist": [
    "Write unit tests (critical)",
    "Add error handling (critical)",
    "Create API documentation (high)",
    "Setup logging (high)",
    "Add database migrations (high)",
    "Implement rate limiting (medium)"
  ],
  "job_application_timeline": [
    {{"week": 14, "action": "Start applying to junior roles"}},
    {{"week": 16, "action": "Refine portfolio with latest projects"}},
    {{"week": 18, "action": "Start interviewing"}},
    {{"week": 20, "action": "Target offer date"}}
  ],
  "total_weeks": 20,
  "job_ready_date": "Estimated date to be job-ready",
  "success_metrics": [
    "Can build API from scratch",
    "Can design database schema",
    "Can deploy to production",
    "Can explain architectural decisions",
    "Pass 80%+ of technical interviews"
  ],
  "motivation_message": "You're building real products that people will use. Every week brings you closer to your goal!"
}}

Resume/Current Skills:
{resume_text[:2000]}

Job Descriptions:
{combined_jds[:3000]}

Experience Level: {experience_level}
Hours per week available: {hours_per_week}
Learning preferences: {', '.join(learning_style)}

Create a PRODUCTION-READY roadmap with:
1. Detailed daily activities for first 12 weeks
2. Real project components you can build (not just tutorials)
3. Specific, actionable learning resources
4. Clear tech stack recommendations
5. Deployment milestones
6. Interview prep schedule
7. Technical debt & best practices
Make it realistic for {hours_per_week} hours/week."""

            try:
                # Try models in order with automatic fallback
                models_to_try = [
                    ("llama-3.3-70b-versatile", 5000),
                    ("openai/gpt-oss-120b", 5000),
                    ("llama-3.1-8b-instant", 4000)
                ]
                
                roadmap = None
                last_error = None
                for model, max_tokens in models_to_try:
                    try:
                        roadmap = groq_json(prompt, model=model, max_tokens=max_tokens)
                        break  # Success, exit loop
                    except Exception as e:
                        error_msg = str(e).lower()
                        last_error = e
                        
                        # Retry with next model on rate limits or JSON errors
                        if "rate_limit" in error_msg or "429" in error_msg or "413" in error_msg or "expecting value" in error_msg or "limit" in error_msg:
                            continue  # Try next model
                        else:
                            raise  # Other errors, don't try next model
                
                if roadmap:
                    roadmap_id = save_roadmap(", ".join(roadmap.get("target_roles",[])), roadmap)
                    if "current_roadmap_id" not in st.session_state:
                        st.session_state.current_roadmap_id = roadmap_id
                    st.session_state.current_roadmap = roadmap
                    _render_roadmap(roadmap, roadmap_id)
                else:
                    if last_error:
                        error_str = str(last_error)
                        if "rate_limit" in error_str.lower() or "limit" in error_str.lower():
                            st.error("⏳ **API limit exhausted for today.** All models have reached their daily token limit. Please try again tomorrow!")
                        else:
                            st.error(f"❌ Generation failed: {error_str[:100]}... Please try again.")
                    else:
                        st.error("❌ All models are currently at capacity. Please try again tomorrow!")
            except Exception as e:
                error_str = str(e)
                if "rate_limit" in error_str.lower() or "limit" in error_str.lower():
                    st.error("⏳ **API limit exhausted for today.** All models have reached their daily token limit. Please try again tomorrow!")
                else:
                    st.error(f"Roadmap generation failed: {error_str}")

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

    # Tech Stack Overview
    tech_stack = roadmap.get("tech_stack", {})
    if tech_stack:
        st.markdown("### 🛠️ Recommended Tech Stack")
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            if tech_stack.get("frontend"):
                st.markdown("**Frontend:**")
                for tech in tech_stack["frontend"]:
                    st.markdown(f"→ {tech}")
        with col2:
            if tech_stack.get("backend"):
                st.markdown("**Backend:**")
                for tech in tech_stack["backend"]:
                    st.markdown(f"→ {tech}")
        with col3:
            if tech_stack.get("database"):
                st.markdown("**Database:**")
                for tech in tech_stack["database"]:
                    st.markdown(f"→ {tech}")
        with col4:
            if tech_stack.get("devops"):
                st.markdown("**DevOps:**")
                for tech in tech_stack["devops"]:
                    st.markdown(f"→ {tech}")
        st.markdown("---")

    # Project Development Phases
    project_phases = roadmap.get("project_development_phases", [])
    if project_phases:
        st.markdown("### 🎯 Project Development Phases")
        phase_tabs = st.tabs([m.get("phase", f"Phase {i+1}") for i, m in enumerate(project_phases)])
        
        for i, (tab, milestone) in enumerate(zip(phase_tabs, project_phases)):
            with tab:
                st.markdown(f"**Focus:** {milestone.get('focus', '')}")
                st.markdown(f"**Project Component:** {milestone.get('project_component', '')}")
                
                st.markdown("**Deliverables:**")
                for deliverable in milestone.get("deliverables", []):
                    st.markdown(f"✓ {deliverable}")
                
                st.markdown("**Tech Focus:**")
                for tech in milestone.get("tech_focus", []):
                    st.markdown(f"→ {tech}")
        
        st.markdown("---")

    # Skill gaps with priorities
    gaps = roadmap.get("skill_gaps", [])
    if gaps:
        st.markdown("### 🎯 Your Skill Gaps (Prioritized)")
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

        # Detailed skill gaps
        for gap in gaps:
            priority_color = {"High": "#ef4444", "Medium": "#f59e0b", "Low": "#22c55e"}.get(gap.get("priority","Low"), "#aaa")
            with st.expander(f"{'🔴' if gap.get('priority')=='High' else '🟡' if gap.get('priority')=='Medium' else '🟢'} {gap.get('skill','')} — {gap.get('estimated_weeks',1)} weeks"):
                st.markdown(f"**Why it matters:** {gap.get('reason','')}")
                
                col1, col2 = st.columns(2)
                with col1:
                    st.markdown("**Free Resources:**")
                    for r in gap.get("free_resources", []):
                        st.markdown(f"→ {r}")
                
                with col2:
                    st.markdown("**Paid Resources:**")
                    for r in gap.get("paid_resources", []):
                        st.markdown(f"→ {r}")
                
                st.info(f"🏗️ **Practice Project:** {gap.get('practice_project','')}")
                st.markdown(f"**Goal:** {gap.get('hands_on_goal','')}")
        
        st.markdown("---")

    # Learning Path Options
    learning_paths = roadmap.get("learning_path_options", [])
    if learning_paths:
        st.markdown("### 📚 Learning Path Options")
        for path in learning_paths:
            with st.expander(f"{path.get('path', '')} ({path.get('duration', '')})"):
                st.markdown(f"**Focus:** {path.get('focus', '')}")
                st.markdown(f"**Weekly Commitment:** {path.get('weekly_commitment', '')}")
                st.markdown(f"**Best For:** {path.get('best_for', '')}")
        st.markdown("---")

    # Daily Structure
    daily_structure = roadmap.get("daily_structure", {})
    if daily_structure:
        st.markdown("### 📅 Recommended Daily Structure")
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.info(f"🌅 **Morning**\n{daily_structure.get('morning', '')}")
        with col2:
            st.info(f"☀️ **Midday**\n{daily_structure.get('midday', '')}")
        with col3:
            st.info(f"🌤️ **Afternoon**\n{daily_structure.get('afternoon', '')}")
        with col4:
            st.info(f"🌙 **Evening**\n{daily_structure.get('evening', '')}")
        st.markdown("---")

    st.markdown("### 📅 Week-by-Week Detailed Plan")

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
        difficulty = week.get("difficulty", "")

        with st.expander(f"{icon} Week {week_num}: {week.get('theme','')} ({week.get('hours_needed',0)} hrs) — {difficulty}", expanded=False):
            col_l, col_r = st.columns([3, 1])
            with col_l:
                st.markdown(f"**Phase:** {week.get('phase', '')}")
                
                skills = week.get("skills", [])
                if skills:
                    st.markdown("**Skills to Master:**")
                    for skill in skills:
                        st.markdown(f"→ {skill}")

                daily = week.get("daily_tasks", [])
                if daily:
                    st.markdown("**Daily Tasks:**")
                    for i, task in enumerate(daily, 1):
                        st.markdown(f"{i}. {task}")

                if week.get("project"):
                    st.warning(f"🏗️ **Main Project:** {week['project']}")
                
                if week.get("project_details"):
                    st.markdown(f"**Details:** {week.get('project_details', '')}")
                
                if week.get("learning_resources"):
                    st.markdown("**Learning Resources:**")
                    for res in week.get("learning_resources", []):
                        res_type = res.get("type", "Resource")
                        name = res.get("name", "")
                        platform = res.get("platform", "")
                        time = res.get("time", "")
                        st.markdown(f"→ [{res_type}] {name} on {platform} ({time})")
                
                if week.get("milestone"):
                    st.success(f"🏆 **Milestone:** {week['milestone']}")
                
                if week.get("checkpoint"):
                    st.info(f"✅ **Checkpoint:** {week['checkpoint']}")

            with col_r:
                done = st.checkbox("Mark Complete", value=is_done, key=f"week_check_{week_num}")
                st.session_state.roadmap_progress[f"week_{week_num}"] = done

    st.markdown("---")

    # Hands-on Projects
    hands_on = roadmap.get("hands_on_projects", [])
    if hands_on:
        st.markdown("### 💻 Real-World Projects You'll Build")
        for project in hands_on:
            with st.expander(f"🚀 {project.get('name', '')} ({project.get('estimated_weeks', '')} weeks)"):
                st.markdown(f"**Description:** {project.get('description', '')}")
                st.markdown(f"**Learning Outcomes:**")
                for outcome in project.get("learning_outcomes", []):
                    st.markdown(f"→ {outcome}")
                
                st.markdown("**Tech Stack:**")
                for tech in project.get("tech_stack", []):
                    st.markdown(f"→ {tech}")
                
                st.markdown("**Modules to Build:**")
                for module in project.get("modules", []):
                    st.markdown(f"✓ {module}")
                
                if project.get("phases"):
                    st.markdown("**Development Phases:**")
                    for phase in project.get("phases", []):
                        st.markdown(f"→ {phase}")
        st.markdown("---")

    # Monthly milestones
    milestones = roadmap.get("monthly_milestones", [])
    if milestones:
        st.markdown("### 🏆 Monthly Milestones")
        for i, m in enumerate(milestones, 1):
            st.markdown(f"**{m}**")

    # Certifications
    certs = roadmap.get("certifications_path", [])
    if certs:
        st.markdown("### 📜 Certification Path")
        for cert in certs:
            cost_badge = f"🆓 Free" if cert.get("free") else f"💰 ${cert.get('cost', 'TBD')}"
            st.markdown(f"→ **{cert.get('name','')}** on {cert.get('platform','')} | {cost_badge} | {cert.get('weeks',0)} weeks")

    # Quick wins
    quick_wins = roadmap.get("quick_wins", [])
    if quick_wins:
        st.markdown("### ⚡ Quick Wins (Learn in Days)")
        for win in quick_wins:
            st.success(f"✨ {win}")

    # Interview Prep Schedule
    interview_prep = roadmap.get("interview_prep_schedule", [])
    if interview_prep:
        st.markdown("### 🎤 Interview Prep Schedule")
        for prep in interview_prep:
            st.markdown(f"**Week {prep.get('week', '')}:** {prep.get('focus', '')} ({prep.get('time', '')})")

    # Technical Debt Checklist
    tech_debt = roadmap.get("technical_debt_checklist", [])
    if tech_debt:
        st.markdown("### ✅ Technical Debt & Best Practices")
        for item in tech_debt:
            st.markdown(f"→ {item}")

    # Job Application Timeline
    job_timeline = roadmap.get("job_application_timeline", [])
    if job_timeline:
        st.markdown("### 📈 Job Application Timeline")
        for timeline in job_timeline:
            st.markdown(f"**Week {timeline.get('week', '')}:** {timeline.get('action', '')}")

    # Success Metrics
    success_metrics = roadmap.get("success_metrics", [])
    if success_metrics:
        st.markdown("### 🎯 Success Metrics")
        for metric in success_metrics:
            st.markdown(f"✓ {metric}")

    st.markdown("---")

    # Export
    sections = [
        {"heading": "Target Roles", "content": roadmap.get("target_roles",[])},
        {"heading": "Tech Stack", "content": [f"{k.upper()}: {', '.join(v) if isinstance(v, list) else v}" for k, v in tech_stack.items()] if tech_stack else []},
        {"heading": "Skill Gaps", "content": [f"{g.get('skill','')} ({g.get('priority','')} priority, {g.get('estimated_weeks',1)} weeks)" for g in gaps]},
        {"heading": "Project Development Phases", "content": [f"{m.get('phase', '')} - {m.get('focus', '')}" for m in project_phases]},
        {"heading": "Weekly Plan Summary", "content": [f"Week {w.get('week',0)}: {w.get('theme','')} — {w.get('milestone','')}" for w in weekly_plan[:12]]},
        {"heading": "Monthly Milestones", "content": milestones},
        {"heading": "Certifications", "content": [f"{c.get('name','')} — {c.get('platform','')} ({'Free' if c.get('free') else 'Paid'})" for c in certs]},
        {"heading": "Quick Wins", "content": quick_wins},
        {"heading": "Interview Prep Schedule", "content": [f"Week {p.get('week', '')}: {p.get('focus', '')}" for p in interview_prep]},
        {"heading": "Success Metrics", "content": success_metrics},
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
