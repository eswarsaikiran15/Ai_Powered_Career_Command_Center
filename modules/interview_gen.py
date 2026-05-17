import json
import streamlit as st
from datetime import datetime
from utils.groq_helper import groq_json
from utils.db import get_conn
from utils.exports import export_docx, export_pdf


def save_session(role: str, company: str, questions: dict):
    try:
        conn = get_conn()
        c = conn.cursor()
        c.execute("INSERT INTO interview_sessions (role, company, questions_json) VALUES (?,?,?)",
                  (role, company, json.dumps(questions)))
        conn.commit()
        conn.close()
    except Exception as e:
        pass


def run():
    st.markdown("## 🎤 Interview Question Generator")
    st.caption("Get role-specific, company-specific interview questions with ideal answer frameworks.")

    col1, col2 = st.columns(2)
    with col1:
        role = st.text_input("🎯 Target Role", placeholder="e.g. Data Analyst, Python Developer")
    with col2:
        company = st.text_input("🏢 Company Name (Optional)", placeholder="e.g. Google, TCS, Infosys")

    jd_text = st.text_area("📋 Paste Job Description (Optional — improves accuracy)",
                            height=150, placeholder="Paste JD here for more targeted questions...")

    level = st.selectbox("Experience Level", ["Fresher (0-1 years)", "Junior (1-3 years)", "Mid (3-5 years)", "Senior (5+ years)"])

    q_types = st.multiselect("Question Types", [
        "Technical", "Behavioral", "Situational", "HR/Cultural", "Case Study", "Coding"
    ], default=["Technical", "Behavioral", "HR/Cultural"])

    num_questions = st.slider("Number of Questions", 5, 25, 15)

    if st.button("🎯 Generate Questions", type="primary", use_container_width=True,
                 disabled=not role):
        with st.spinner("Generating your personalized interview prep..."):
            prompt = f"""You are an expert interview coach. Generate interview questions and return ONLY valid JSON:
{{
  "technical": [
    {{"question": "Q?", "difficulty": "Medium", "ideal_answer_framework": "How to answer this...", "red_flags": "What not to say"}}
  ],
  "behavioral": [
    {{"question": "Q?", "star_method": "Situation, Task, Action, Result guidance", "what_they_assess": "What this reveals"}}
  ],
  "situational": [
    {{"question": "Q?", "ideal_approach": "How to approach this"}}
  ],
  "hr_cultural": [
    {{"question": "Q?", "tip": "How to answer"}}
  ],
  "coding": [
    {{"question": "Q?", "topic": "Arrays/SQL/etc", "hint": "Approach hint"}}
  ],
  "questions_to_ask_interviewer": ["Q1?", "Q2?", "Q3?"],
  "salary_negotiation_tips": ["tip1", "tip2"],
  "common_mistakes": ["mistake1", "mistake2", "mistake3"],
  "preparation_checklist": ["item1", "item2", "item3", "item4", "item5"]
}}

Role: {role}
Company: {company or 'Not specified'}
Level: {level}
Question Types Needed: {', '.join(q_types)}
Total Questions Needed: {num_questions}
Job Description: {jd_text[:2000] if jd_text else 'Not provided'}

Generate {num_questions} total questions distributed across the requested types."""

            try:
                result = groq_json(prompt, max_tokens=3000)
                save_session(role, company, result)
                _render_questions(result, role, company)
            except Exception as e:
                st.error(f"Generation failed: {e}")

    # History
    with st.expander("📚 Previous Sessions"):
        try:
            conn = get_conn()
            c = conn.cursor()
            c.execute("SELECT id, timestamp, role, company FROM interview_sessions ORDER BY timestamp DESC LIMIT 10")
            rows = c.fetchall()
            conn.close()
            if rows:
                for row in rows:
                    st.markdown(f"**{row[2]}** at **{row[3] or 'N/A'}** — {row[1]}")
            else:
                st.info("No sessions yet.")
        except:
            pass


def _render_questions(result: dict, role: str, company: str):
    st.markdown("---")
    st.markdown(f"## 🎤 Interview Prep: {role}" + (f" @ {company}" if company else ""))

    tabs = st.tabs(["🔧 Technical", "🧠 Behavioral", "📋 Situational",
                    "🤝 HR/Cultural", "💻 Coding", "📝 Checklist"])

    with tabs[0]:
        for i, q in enumerate(result.get("technical", []), 1):
            with st.expander(f"Q{i}. {q.get('question', '')}"):
                st.markdown(f"**Difficulty:** {q.get('difficulty', 'Medium')}")
                st.markdown(f"**How to Answer:** {q.get('ideal_answer_framework', '')}")
                if q.get('red_flags'):
                    st.error(f"❌ Avoid: {q.get('red_flags', '')}")

    with tabs[1]:
        for i, q in enumerate(result.get("behavioral", []), 1):
            with st.expander(f"Q{i}. {q.get('question', '')}"):
                st.info(f"⭐ STAR Method: {q.get('star_method', '')}")
                st.markdown(f"**What they assess:** {q.get('what_they_assess', '')}")

    with tabs[2]:
        for i, q in enumerate(result.get("situational", []), 1):
            with st.expander(f"Q{i}. {q.get('question', '')}"):
                st.markdown(f"**Approach:** {q.get('ideal_approach', '')}")

    with tabs[3]:
        for i, q in enumerate(result.get("hr_cultural", []), 1):
            with st.expander(f"Q{i}. {q.get('question', '')}"):
                st.markdown(f"**Tip:** {q.get('tip', '')}")

    with tabs[4]:
        for i, q in enumerate(result.get("coding", []), 1):
            with st.expander(f"Q{i}. {q.get('question', '')}"):
                st.markdown(f"**Topic:** `{q.get('topic', '')}`")
                st.markdown(f"**Hint:** {q.get('hint', '')}")

    with tabs[5]:
        checklist = result.get("preparation_checklist", [])
        if "interview_checklist" not in st.session_state:
            st.session_state.interview_checklist = {item: False for item in checklist}

        st.markdown("### ✅ Preparation Checklist")
        for item in checklist:
            checked = st.checkbox(item, key=f"chk_{item}")
            st.session_state.interview_checklist[item] = checked

        done = sum(st.session_state.interview_checklist.values())
        st.progress(done / max(len(checklist), 1))
        st.caption(f"{done}/{len(checklist)} completed")

        st.markdown("### 💬 Questions to Ask Interviewer")
        for q in result.get("questions_to_ask_interviewer", []):
            st.markdown(f"→ {q}")

        st.markdown("### ⚠️ Common Mistakes to Avoid")
        for m in result.get("common_mistakes", []):
            st.error(f"❌ {m}")

    st.markdown("---")
    # Export
    all_questions = []
    for section in ["technical", "behavioral", "situational", "hr_cultural", "coding"]:
        for q in result.get(section, []):
            all_questions.append(q.get("question", ""))

    sections = [
        {"heading": f"Interview Prep: {role}" + (f" @ {company}" if company else ""),
         "content": f"Generated on {datetime.now().strftime('%B %d, %Y')}"},
        {"heading": "Technical Questions", "content": [q.get("question","") for q in result.get("technical",[])]},
        {"heading": "Behavioral Questions", "content": [q.get("question","") for q in result.get("behavioral",[])]},
        {"heading": "HR/Cultural Questions", "content": [q.get("question","") for q in result.get("hr_cultural",[])]},
        {"heading": "Questions to Ask Interviewer", "content": result.get("questions_to_ask_interviewer",[])},
        {"heading": "Preparation Checklist", "content": result.get("preparation_checklist",[])},
        {"heading": "Common Mistakes to Avoid", "content": result.get("common_mistakes",[])},
    ]

    c1, c2 = st.columns(2)
    with c1:
        st.download_button("📄 Download DOCX",
                           export_docx("Interview Preparation Guide", sections),
                           file_name=f"interview_prep_{role.replace(' ','_')}.docx",
                           mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                           use_container_width=True)
    with c2:
        st.download_button("📥 Download PDF",
                           export_pdf("Interview Preparation Guide", sections),
                           file_name=f"interview_prep_{role.replace(' ','_')}.pdf",
                           mime="application/pdf",
                           use_container_width=True)
