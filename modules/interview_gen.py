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

    col_nq, col_mod = st.columns(2)
    with col_nq:
        num_questions = st.slider("Number of Questions", 5, 25, 15)
    with col_mod:
        selected_model = st.selectbox("AI Model", [
            "llama-3.3-70b-versatile",
            "llama-3.1-8b-instant",
            "mixtral-8x7b-32768",
            "gemma2-9b-it"
        ], help="Change the model if you encounter rate limits (e.g., Code 429).")

    if st.button("🎯 Generate Questions", type="primary", use_container_width=True,
                 disabled=not role):
        with st.spinner("Generating your personalized interview prep with detailed answers..."):
            prompt = f"""You are an expert interview coach and hiring manager. Generate comprehensive interview questions with DETAILED ANSWERS. Return ONLY valid JSON:
{{
  "technical": [
    {{
      "question": "Q?", 
      "difficulty": "Easy/Medium/Hard", 
      "sample_answer": "Detailed answer example (3-5 sentences)",
      "key_points": ["point1", "point2", "point3"],
      "ideal_answer_framework": "Structure to follow",
      "example_response": "Here's what a strong answer sounds like: ...",
      "red_flags": "What hiring managers look for as negatives",
      "follow_up_questions": ["Why did you choose that approach?", "How would you optimize it?"],
      "time_to_answer": "2-3 minutes"
    }}
  ],
  "behavioral": [
    {{
      "question": "Q?",
      "star_method": "Specific situation, Task required, Action taken, Result achieved",
      "sample_answer": "Detailed STAR example (4-6 sentences)",
      "what_they_assess": "What skill or competency this reveals",
      "strong_answer_tips": ["Tip 1", "Tip 2", "Tip 3"],
      "example_response": "A strong answer would start with: ...",
      "metrics_to_mention": "Quantifiable results to highlight",
      "common_mistakes": ["Don't do this...", "Avoid saying..."],
      "follow_up_questions": ["What did you learn?", "Would you do it differently?"]
    }}
  ],
  "situational": [
    {{
      "question": "What would you do if...?",
      "ideal_approach": "Step-by-step problem-solving approach",
      "sample_answer": "Here's how you should approach this scenario",
      "key_steps": ["Step 1: Assess", "Step 2: Plan", "Step 3: Execute"],
      "example_response": "I would first... then... finally...",
      "what_to_avoid": "Common mistakes in this scenario",
      "communication_tips": ["How to explain your thinking"],
      "follow_up_questions": ["What if this constraint existed?"]
    }}
  ],
  "system_design": [
    {{
      "question": "Design [system]?",
      "core_concepts": ["Concept 1", "Concept 2"],
      "architecture_overview": "Brief architecture description",
      "key_components": ["Component 1", "Component 2"],
      "scalability_considerations": "How to scale this system",
      "tradeoffs": ["Pro: X | Con: Y"],
      "sample_approach": "Detailed step-by-step design explanation",
      "technologies_mentioned": ["Tech 1", "Tech 2"],
      "follow_up_questions": ["What if traffic doubles?", "How do you handle failures?"]
    }}
  ],
  "hr_cultural": [
    {{
      "question": "Q?",
      "sample_answer": "Detailed answer example",
      "company_research_tip": "Research this about the company before answering",
      "values_alignment": "What company values this shows",
      "strong_answer_tips": ["Tip 1", "Tip 2"],
      "what_to_avoid": "Common pitfalls",
      "example_response": "A compelling answer might be: ...",
      "follow_up_questions": ["Can you give a specific example?"]
    }}
  ],
  "coding": [
    {{
      "question": "Q?",
      "topic": "Arrays/Strings/SQL/APIs/Database/etc",
      "difficulty": "Easy/Medium/Hard",
      "problem_breakdown": "How to approach the problem",
      "solution_approach": "Algorithm or step-by-step solution",
      "code_template": "Pseudocode or actual code",
      "time_complexity": "O(n) or similar",
      "space_complexity": "O(n) or similar",
      "test_cases": ["Test case 1", "Test case 2"],
      "optimization_tips": ["Optimization 1", "Optimization 2"],
      "follow_up_questions": ["How to optimize further?", "Alternative approach?"],
      "resources": ["LeetCode link or similar"]
    }}
  ],
  "hr_red_flags": [
    {{
      "flag": "Describing yourself negatively",
      "impact": "What hiring managers think",
      "better_approach": "How to reframe positively"
    }}
  ],
  "questions_to_ask_interviewer": [
    {{
      "question": "Q?",
      "why_ask": "What this shows about you",
      "good_time_to_ask": "When in the interview"
    }}
  ],
  "salary_negotiation_tips": ["tip1", "tip2", "tip3", "tip4"],
  "company_research_checklist": ["What to research about the company"],
  "day_before_tips": ["Sleep well", "Prepare materials", "Review these questions"],
  "on_interview_day": ["Arrive 15 min early", "Dress professionally", "Bring copies of resume"],
  "preparation_checklist": ["Mock interviews done", "Researched company", "Prepared stories", "Know your resume", "Practice technical questions", "Prepared questions to ask", "Know location and route", "Good night sleep"],
  "confidence_boosters": ["Remember your past achievements", "You've prepared thoroughly", "This is a two-way conversation"]
}}

Role: {role}
Company: {company or 'Not specified'}
Level: {level}
Question Types: {', '.join(q_types)}
Total Questions: {num_questions}
Job Description: {jd_text[:2000] if jd_text else 'Not provided'}

CRITICAL INSTRUCTIONS:
1. You MUST generate EXACTLY {num_questions} detailed questions in total, distributed across the requested categories. 
2. DO NOT take shortcuts, do NOT be lazy, and do NOT omit answers. 
3. I am programmatically validating the array lengths to ensure exactly {num_questions} questions exist.
4. For every single question, provide:
   - Clear, specific question
   - Detailed sample answer (3-6 sentences)
   - Key points to hit
   - What hiring managers assess
   - Common mistakes to avoid
   - Follow-up questions they might ask

Make answers comprehensive, realistic, and interview-ready. Include specific examples where applicable."""

            try:
                result = groq_json(prompt, model=selected_model, max_tokens=7000)
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
            
            if rows:
                for row in rows:
                    hc1, hc2 = st.columns([5, 1])
                    with hc1:
                        st.markdown(f"**{row[2]}** at **{row[3] or 'N/A'}** — {row[1]}")
                    with hc2:
                        if st.button("🗑️", key=f"del_interview_{row[0]}", help="Delete session"):
                            c.execute("DELETE FROM interview_sessions WHERE id = ?", (row[0],))
                            conn.commit()
                            st.rerun()
            else:
                st.info("No sessions yet.")
            conn.close()
        except:
            pass


def _render_questions(result: dict, role: str, company: str):
    st.markdown("---")
    st.markdown(f"## 🎤 Interview Prep: {role}" + (f" @ {company}" if company else ""))

    # Confidence message
    if result.get("confidence_boosters"):
        with st.expander("💪 Confidence Boosters Before Your Interview"):
            for booster in result.get("confidence_boosters", []):
                st.success(booster)

    # Day before tips
    if result.get("day_before_tips"):
        st.info("📋 **Before Your Interview Day:**")
        for tip in result.get("day_before_tips", []):
            st.markdown(f"✓ {tip}")

    tabs = st.tabs(["🔧 Technical", "🧠 Behavioral", "📋 Situational", "🏗️ System Design",
                    "🤝 HR/Cultural", "💻 Coding", "📝 Checklist", "❓ Ask Them"])

    with tabs[0]:
        st.markdown("### Technical Questions with Detailed Answers")
        for i, q in enumerate(result.get("technical", []), 1):
            with st.expander(f"Q{i}. {q.get('question', '')} — {q.get('difficulty', 'Medium')}", expanded=False):
                col1, col2 = st.columns([1, 1])
                
                with col1:
                    st.markdown("**⏱️ Time to Answer:** " + q.get('time_to_answer', '2-3 min'))
                    st.markdown("**🎯 Difficulty:** " + q.get('difficulty', 'Medium'))
                
                with col2:
                    st.markdown("**Key Skills Tested:**")
                    for point in q.get('key_points', [])[:3]:
                        st.markdown(f"→ {point}")
                
                st.divider()
                st.markdown("### 📝 Sample Answer:")
                st.info(q.get('sample_answer', ''))
                
                if q.get('example_response'):
                    st.markdown("### 💬 Example Response:")
                    st.write(q.get('example_response', ''))
                
                st.markdown("### 🔑 Key Points to Mention:")
                for point in q.get('key_points', []):
                    st.markdown(f"• {point}")
                
                st.markdown("### 📚 How to Structure Your Answer:")
                st.markdown(q.get('ideal_answer_framework', ''))
                
                if q.get('red_flags'):
                    st.error("❌ **Red Flags (Avoid Saying):**\n" + q.get('red_flags', ''))
                
                if q.get('follow_up_questions'):
                    st.markdown("### 🔄 Potential Follow-Up Questions:")
                    for followup in q.get('follow_up_questions', []):
                        st.markdown(f"→ {followup}")

    with tabs[1]:
        st.markdown("### Behavioral Questions with STAR Method")
        for i, q in enumerate(result.get("behavioral", []), 1):
            with st.expander(f"Q{i}. {q.get('question', '')}", expanded=False):
                st.markdown("### ⭐ STAR Method Breakdown:")
                st.info(q.get('star_method', ''))
                
                st.divider()
                st.markdown("### 📝 Sample STAR Answer:")
                st.info(q.get('sample_answer', ''))
                
                if q.get('example_response'):
                    st.markdown("### 💬 Example of Strong Answer:")
                    st.write(q.get('example_response', ''))
                
                st.markdown("### 🎯 What They're Assessing:")
                st.markdown(q.get('what_they_assess', ''))
                
                st.markdown("### 💡 Tips for Strong Answer:")
                for tip in q.get('strong_answer_tips', []):
                    st.markdown(f"✓ {tip}")
                
                if q.get('metrics_to_mention'):
                    st.success(f"📊 **Metrics to Mention:** {q.get('metrics_to_mention', '')}")
                
                if q.get('common_mistakes'):
                    st.error("❌ **Common Mistakes:**")
                    for mistake in q.get('common_mistakes', []):
                        st.markdown(f"→ {mistake}")
                
                if q.get('follow_up_questions'):
                    st.markdown("### 🔄 Follow-Up Questions They Might Ask:")
                    for followup in q.get('follow_up_questions', []):
                        st.markdown(f"→ {followup}")

    with tabs[2]:
        st.markdown("### Situational Questions - Problem-Solving Approach")
        for i, q in enumerate(result.get("situational", []), 1):
            with st.expander(f"Q{i}. {q.get('question', '')}", expanded=False):
                st.markdown("### 🎯 Ideal Approach:")
                st.info(q.get('ideal_approach', ''))
                
                st.divider()
                st.markdown("### 📝 Sample Answer:")
                st.write(q.get('sample_answer', ''))
                
                if q.get('example_response'):
                    st.markdown("### 💬 How to Explain Your Thinking:")
                    st.write(q.get('example_response', ''))
                
                if q.get('key_steps'):
                    st.markdown("### 📋 Step-by-Step Approach:")
                    for step in q.get('key_steps', []):
                        st.markdown(f"→ {step}")
                
                if q.get('what_to_avoid'):
                    st.error(f"❌ **What to Avoid:** {q.get('what_to_avoid', '')}")
                
                if q.get('communication_tips'):
                    st.markdown("### 💬 Communication Tips:")
                    for tip in q.get('communication_tips', []):
                        st.markdown(f"✓ {tip}")
                
                if q.get('follow_up_questions'):
                    st.markdown("### 🔄 Follow-Ups:")
                    for followup in q.get('follow_up_questions', []):
                        st.markdown(f"→ {followup}")

    with tabs[3]:
        system_design_qs = result.get("system_design", [])
        if system_design_qs:
            st.markdown("### System Design Problems - Architecture Focus")
            for i, q in enumerate(system_design_qs, 1):
                with st.expander(f"Q{i}. {q.get('question', '')}", expanded=False):
                    st.markdown("### 🏗️ Architecture Overview:")
                    st.info(q.get('architecture_overview', ''))
                    
                    st.markdown("### 🧩 Core Concepts:")
                    for concept in q.get('core_concepts', []):
                        st.markdown(f"→ {concept}")
                    
                    st.markdown("### 📦 Key Components:")
                    for comp in q.get('key_components', []):
                        st.markdown(f"→ {comp}")
                    
                    st.divider()
                    st.markdown("### 💡 Detailed Approach:")
                    st.write(q.get('sample_approach', ''))
                    
                    st.markdown("### 📊 Scalability Considerations:")
                    st.info(q.get('scalability_considerations', ''))
                    
                    if q.get('tradeoffs'):
                        st.markdown("### ⚖️ Trade-offs to Discuss:")
                        for tradeoff in q.get('tradeoffs', []):
                            st.markdown(f"→ {tradeoff}")
                    
                    if q.get('technologies_mentioned'):
                        st.markdown("### 🔧 Technologies to Mention:")
                        for tech in q.get('technologies_mentioned', []):
                            st.markdown(f"→ {tech}")
                    
                    if q.get('follow_up_questions'):
                        st.markdown("### 🔄 Follow-Ups They Might Ask:")
                        for followup in q.get('follow_up_questions', []):
                            st.markdown(f"→ {followup}")
        else:
            st.info("No system design questions for this role.")

    with tabs[4]:
        st.markdown("### HR & Cultural Fit Questions")
        for i, q in enumerate(result.get("hr_cultural", []), 1):
            with st.expander(f"Q{i}. {q.get('question', '')}", expanded=False):
                st.markdown("### 📝 Sample Answer:")
                st.info(q.get('sample_answer', ''))
                
                if q.get('example_response'):
                    st.markdown("### 💬 Example of Compelling Answer:")
                    st.write(q.get('example_response', ''))
                
                st.markdown("### 🏢 Company Research Tip:")
                st.warning(q.get('company_research_tip', ''))
                
                if q.get('values_alignment'):
                    st.markdown(f"### 💡 **Values This Shows:** {q.get('values_alignment', '')}")
                
                st.markdown("### ✓ Tips for Strong Answer:")
                for tip in q.get('strong_answer_tips', []):
                    st.markdown(f"✓ {tip}")
                
                if q.get('what_to_avoid'):
                    st.error(f"❌ **What to Avoid:** {q.get('what_to_avoid', '')}")
                
                if q.get('follow_up_questions'):
                    st.markdown("### 🔄 Follow-Ups:")
                    for followup in q.get('follow_up_questions', []):
                        st.markdown(f"→ {followup}")

    with tabs[5]:
        st.markdown("### Coding Questions with Solutions")
        for i, q in enumerate(result.get("coding", []), 1):
            with st.expander(f"Q{i}. {q.get('question', '')} — {q.get('difficulty', 'Medium')}", expanded=False):
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.metric("Difficulty", q.get('difficulty', 'Medium'))
                with col2:
                    st.metric("Time Complexity", q.get('time_complexity', 'N/A'))
                with col3:
                    st.metric("Space Complexity", q.get('space_complexity', 'N/A'))
                
                st.divider()
                st.markdown("### 📌 Topic: " + q.get('topic', ''))
                
                st.markdown("### 🤔 Problem Breakdown:")
                st.info(q.get('problem_breakdown', ''))
                
                st.markdown("### 💡 Solution Approach:")
                st.write(q.get('solution_approach', ''))
                
                if q.get('code_template'):
                    st.markdown("### 📝 Code Template:")
                    st.code(q.get('code_template', ''), language='python')
                
                if q.get('test_cases'):
                    st.markdown("### ✅ Test Cases:")
                    for test in q.get('test_cases', []):
                        st.markdown(f"→ {test}")
                
                if q.get('optimization_tips'):
                    st.markdown("### ⚡ Optimization Tips:")
                    for opt in q.get('optimization_tips', []):
                        st.markdown(f"→ {opt}")
                
                if q.get('resources'):
                    st.markdown("### 📚 Resources:")
                    for res in q.get('resources', []):
                        st.markdown(f"→ {res}")
                
                if q.get('follow_up_questions'):
                    st.markdown("### 🔄 Follow-Ups:")
                    for followup in q.get('follow_up_questions', []):
                        st.markdown(f"→ {followup}")

    with tabs[6]:
        checklist = result.get("preparation_checklist", [])
        if "interview_checklist" not in st.session_state:
            st.session_state.interview_checklist = {item: False for item in checklist}

        st.markdown("### ✅ Preparation Checklist")
        st.markdown("**Track your interview preparation progress:**")
        
        for item in checklist:
            checked = st.checkbox(item, key=f"chk_{item}")
            st.session_state.interview_checklist[item] = checked

        done = sum(st.session_state.interview_checklist.values())
        st.progress(done / max(len(checklist), 1))
        st.caption(f"{done}/{len(checklist)} completed ({int((done/max(len(checklist), 1))*100)}%)")
        
        # Day of interview tips
        if result.get("on_interview_day"):
            st.markdown("---")
            st.markdown("### 🎯 On Interview Day:")
            for tip in result.get("on_interview_day", []):
                st.markdown(f"✓ {tip}")

    with tabs[7]:
        st.markdown("### ❓ Questions You Should Ask Them")
        st.info("Asking smart questions shows you're genuinely interested and thinking strategically about the role.")
        
        questions_to_ask = result.get("questions_to_ask_interviewer", [])
        if questions_to_ask and isinstance(questions_to_ask[0], dict):
            for i, qa in enumerate(questions_to_ask, 1):
                with st.expander(f"Q{i}. {qa.get('question', '')}"):
                    st.markdown(f"**Why ask this:** {qa.get('why_ask', '')}")
                    if qa.get('good_time_to_ask'):
                        st.caption(f"⏱️ Good time: {qa.get('good_time_to_ask', '')}")
        else:
            # Fallback for list format
            for i, q in enumerate(questions_to_ask or [], 1):
                st.markdown(f"{i}. {q}")
        
        # HR Red flags
        if result.get("hr_red_flags"):
            st.markdown("---")
            st.error("### ⚠️ Red Flags to Avoid")
            for flag in result.get("hr_red_flags", []):
                with st.expander(f"❌ {flag.get('flag', '')}"):
                    st.markdown(f"**Impact:** {flag.get('impact', '')}")
                    st.success(f"**Better approach:** {flag.get('better_approach', '')}")
        
        # Salary negotiation
        if result.get("salary_negotiation_tips"):
            st.markdown("---")
            st.markdown("### 💰 Salary Negotiation Tips")
            for i, tip in enumerate(result.get("salary_negotiation_tips", []), 1):
                st.markdown(f"{i}. {tip}")

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
