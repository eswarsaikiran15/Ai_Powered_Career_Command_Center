import os
import json
import requests
import streamlit as st
from datetime import datetime
from utils.groq_helper import groq_text
from utils.db import get_conn
from utils.exports import export_docx, export_pdf


def fetch_company_news(company: str) -> str:
    """Fetch recent company news from NewsAPI."""
    api_key = os.getenv("NEWS_API_KEY", "")
    if not api_key:
        return ""
    try:
        url = f"https://newsapi.org/v2/everything?q={company}&sortBy=publishedAt&pageSize=3&apiKey={api_key}"
        res = requests.get(url, timeout=8)
        data = res.json()
        articles = data.get("articles", [])
        summaries = []
        for a in articles[:3]:
            summaries.append(f"- {a.get('title','')}: {a.get('description','')}")
        return "\n".join(summaries)
    except:
        return ""


def save_cover_letter(company: str, role: str, letters: dict):
    try:
        conn = get_conn()
        c = conn.cursor()
        c.execute("INSERT INTO cover_letters (company, role, formal, conversational, bold) VALUES (?,?,?,?,?)",
                  (company, role, letters.get("formal",""), letters.get("conversational",""), letters.get("bold","")))
        conn.commit()
        conn.close()
    except:
        pass


def delete_cover_letter(timestamp: str):
    """Delete a specific cover letter from database."""
    try:
        conn = get_conn()
        c = conn.cursor()
        c.execute("DELETE FROM cover_letters WHERE timestamp = ?", (timestamp,))
        conn.commit()
        conn.close()
        return True
    except:
        return False


def run():
    st.markdown("## ✉️ Cover Letter Writer")
    st.caption("AI writes 3 versions of your cover letter — personalized with real company news.")

    col1, col2 = st.columns(2)
    with col1:
        company = st.text_input("🏢 Company Name", placeholder="e.g. Google, Infosys, Swiggy")
    with col2:
        role = st.text_input("🎯 Role Applying For", placeholder="e.g. Data Analyst")

    hiring_manager = st.text_input("👤 Hiring Manager Name (Optional)", placeholder="e.g. Mr. Rahul Sharma")

    resume_text = st.text_area("📄 Your Resume / Key Points",
                                height=180, placeholder="Paste your resume or key highlights...")
    jd_text = st.text_area("📋 Job Description",
                            height=150, placeholder="Paste the job description...")

    tone_pref = st.radio("Your Preferred Tone",
                         ["Generate All 3 Versions", "Formal Only", "Conversational Only", "Bold Only"],
                         horizontal=True)

    if st.button("✍️ Write Cover Letter", type="primary", use_container_width=True,
                 disabled=not (company and role and resume_text)):

        with st.spinner("Fetching company news and writing your cover letter..."):
            news = fetch_company_news(company)
            news_context = f"\nRecent company news:\n{news}" if news else ""

            prompt = f"""You are an expert cover letter writer. Write 3 versions of a cover letter.
Return ONLY valid JSON:
{{
  "formal": "Full formal cover letter text here...",
  "conversational": "Full conversational cover letter text here...",
  "bold": "Full bold/confident cover letter text here...",
  "subject_line": "Email subject line for this application",
  "linkedin_message": "Short LinkedIn connection request message (under 300 chars)",
  "cold_email": "Cold email to hiring manager if no job posting",
  "follow_up": "Follow-up email to send after 1 week of no reply"
}}

Company: {company}
Role: {role}
Hiring Manager: {hiring_manager or 'Not specified'}
{news_context}

Candidate Resume/Background:
{resume_text[:2000]}

Job Description:
{jd_text[:1500] if jd_text else 'Not provided'}

Rules:
- Each letter must be 3-4 paragraphs, professional, and personalized
- Mention company-specific details if news is provided
- Formal: Traditional professional tone
- Conversational: Warm, human, relatable tone
- Bold: Confident, direct, value-forward tone
- Do NOT use placeholder text like [Your Name] — use "I" and keep it first-person"""

            try:
                # Try models in order with automatic fallback
                models_to_try = [
                    ("llama-3.3-70b-versatile", 3000),
                    ("openai/gpt-oss-120b", 3000),
                    ("llama-3.1-8b-instant", 2500)
                ]
                
                result = None
                last_error = None
                for model, max_tokens in models_to_try:
                    try:
                        result = groq_text(prompt, model=model, max_tokens=max_tokens)
                        break  # Success, exit loop
                    except Exception as e:
                        error_msg = str(e).lower()
                        last_error = e
                        
                        # Retry with next model on rate limits or JSON errors
                        if "rate_limit" in error_msg or "429" in error_msg or "413" in error_msg or "expecting value" in error_msg or "limit" in error_msg:
                            continue  # Try next model
                        else:
                            raise  # Other errors, don't try next model
                
                if result:
                    # Parse JSON from text response
                    import json, re
                    json_match = re.search(r'\{.*\}', result, re.DOTALL)
                    if json_match:
                        letters = json.loads(json_match.group())
                    else:
                        letters = {"formal": result, "conversational": result, "bold": result,
                                   "subject_line": f"Application for {role} at {company}",
                                   "linkedin_message": "", "cold_email": "", "follow_up": ""}

                    save_cover_letter(company, role, letters)
                    _render_letters(letters, company, role)
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
                    st.error(f"Generation failed: {error_str}")

    # History
    with st.expander("📚 Saved Cover Letters"):
        try:
            conn = get_conn()
            c = conn.cursor()
            c.execute("SELECT timestamp, company, role FROM cover_letters ORDER BY timestamp DESC LIMIT 10")
            rows = c.fetchall()
            conn.close()
            if rows:
                for idx, (timestamp, company, role) in enumerate(rows):
                    col_letter, col_del = st.columns([4, 1])
                    with col_letter:
                        st.markdown(f"**{role}** at **{company}** — {timestamp}")
                    with col_del:
                        if st.button("🗑️", key=f"del_letter_{idx}", help="Delete this cover letter"):
                            if delete_cover_letter(timestamp):
                                st.success("✅ Deleted!")
                                st.rerun()
                            else:
                                st.error("❌ Failed to delete")
            else:
                st.info("No saved cover letters yet.")
        except:
            st.info("No history available.")


def _render_letters(letters: dict, company: str, role: str):
    st.markdown("---")
    st.markdown(f"## ✉️ Cover Letters for {role} @ {company}")

    if letters.get("subject_line"):
        st.info(f"📧 **Suggested Subject Line:** {letters['subject_line']}")

    tabs = st.tabs(["📝 Formal", "😊 Conversational", "🔥 Bold",
                    "🔗 LinkedIn Message", "📧 Cold Email", "🔁 Follow-Up"])

    with tabs[0]:
        st.text_area("Formal Version", value=letters.get("formal", ""), height=350, key="cl_formal")
        st.download_button("📄 Download Formal DOCX",
                           export_docx(f"Cover Letter - {role} at {company}",
                                       [{"heading": "Cover Letter", "content": letters.get("formal","")}]),
                           file_name=f"cover_letter_formal_{company.replace(' ','_')}.docx",
                           mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document")

    with tabs[1]:
        st.text_area("Conversational Version", value=letters.get("conversational", ""), height=350, key="cl_conv")
        st.download_button("📄 Download Conversational DOCX",
                           export_docx(f"Cover Letter - {role} at {company}",
                                       [{"heading": "Cover Letter", "content": letters.get("conversational","")}]),
                           file_name=f"cover_letter_conv_{company.replace(' ','_')}.docx",
                           mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document")

    with tabs[2]:
        st.text_area("Bold Version", value=letters.get("bold", ""), height=350, key="cl_bold")
        st.download_button("📄 Download Bold DOCX",
                           export_docx(f"Cover Letter - {role} at {company}",
                                       [{"heading": "Cover Letter", "content": letters.get("bold","")}]),
                           file_name=f"cover_letter_bold_{company.replace(' ','_')}.docx",
                           mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document")

    with tabs[3]:
        st.markdown("### 🔗 LinkedIn Connection Request Message")
        st.text_area("Copy and send on LinkedIn", value=letters.get("linkedin_message", ""), height=120, key="cl_li")
        chars = len(letters.get("linkedin_message", ""))
        st.caption(f"{chars}/300 characters")

    with tabs[4]:
        st.markdown("### 📧 Cold Email to Hiring Manager")
        st.text_area("Use when applying directly", value=letters.get("cold_email", ""), height=250, key="cl_cold")

    with tabs[5]:
        st.markdown("### 🔁 Follow-Up Email (Send after 7 days)")
        st.text_area("Send if no reply after 1 week", value=letters.get("follow_up", ""), height=200, key="cl_follow")

    st.markdown("---")
    # Download all versions
    all_sections = [
        {"heading": "Formal Cover Letter", "content": letters.get("formal","")},
        {"heading": "Conversational Cover Letter", "content": letters.get("conversational","")},
        {"heading": "Bold Cover Letter", "content": letters.get("bold","")},
        {"heading": "LinkedIn Message", "content": letters.get("linkedin_message","")},
        {"heading": "Cold Email", "content": letters.get("cold_email","")},
        {"heading": "Follow-Up Email", "content": letters.get("follow_up","")},
    ]
    st.download_button("📥 Download All Versions as PDF",
                       export_pdf(f"Cover Letter Pack — {role} at {company}", all_sections),
                       file_name=f"cover_letter_pack_{company.replace(' ','_')}.pdf",
                       mime="application/pdf",
                       use_container_width=True)
