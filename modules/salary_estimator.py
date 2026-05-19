import requests
import streamlit as st
import plotly.graph_objects as go
from utils.groq_helper import groq_json


def fetch_country_data(country_name: str) -> dict:
    """Fetch GDP and economic data from World Bank."""
    try:
        # Get country code from RestCountries
        res = requests.get(f"https://restcountries.com/v3.1/name/{country_name}?fields=name,cca2,currencies", timeout=8)
        countries = res.json()
        if not countries or isinstance(countries, dict):
            return {}
        country = countries[0]
        code = country.get("cca2", "")
        currency_info = country.get("currencies", {})
        currency_code = list(currency_info.keys())[0] if currency_info else "USD"

        # Get GDP from World Bank
        wb_res = requests.get(
            f"https://api.worldbank.org/v2/country/{code}/indicator/NY.GDP.PCAP.CD?format=json&mrv=1",
            timeout=8)
        wb_data = wb_res.json()
        gdp_per_capita = None
        if len(wb_data) > 1 and wb_data[1]:
            gdp_per_capita = wb_data[1][0].get("value")

        return {"country": country_name, "code": code,
                "currency": currency_code, "gdp_per_capita": gdp_per_capita}
    except:
        return {"country": country_name, "code": "", "currency": "USD", "gdp_per_capita": None}


def get_exchange_rate(from_currency: str, to_currency: str) -> float:
    """Get exchange rate using Frankfurter API."""
    try:
        res = requests.get(f"https://api.frankfurter.app/latest?from={from_currency}&to={to_currency}", timeout=8)
        data = res.json()
        return data.get("rates", {}).get(to_currency, 1.0)
    except:
        return 1.0


def run():
    st.markdown("## 💰 Salary Estimator")
    st.caption("AI-powered salary estimation based on role, experience, and real economic data.")

    col1, col2, col3 = st.columns(3)
    with col1:
        role = st.text_input("🎯 Role", placeholder="e.g. Data Analyst")
    with col2:
        experience = st.selectbox("Experience Level", [
            "Fresher (0-1 years)", "Junior (1-3 years)",
            "Mid-Level (3-5 years)", "Senior (5-8 years)", "Lead (8+ years)"
        ])
    with col3:
        skills = st.text_input("🔧 Key Skills", placeholder="e.g. Python, SQL, Tableau")

    st.markdown("### 🌍 Compare Across Countries")
    countries = []
    c1, c2, c3 = st.columns(3)
    with c1:
        countries.append(st.text_input("Country 1", value="India"))
    with c2:
        countries.append(st.text_input("Country 2", value="United States"))
    with c3:
        countries.append(st.text_input("Country 3", value="United Kingdom"))

    display_currency = st.selectbox("Display Currency", ["INR", "USD", "EUR", "GBP", "AED"], index=1)

    if st.button("💰 Estimate Salary", type="primary", use_container_width=True, disabled=not role):
        with st.spinner("Fetching economic data and calculating salary estimates..."):

            country_data = []
            for country in countries:
                if country:
                    data = fetch_country_data(country)
                    country_data.append(data)

            country_context = "\n".join([
                f"- {d['country']}: GDP per capita = ${d.get('gdp_per_capita', 'Unknown')}, Currency = {d.get('currency','USD')}"
                for d in country_data
            ])

            prompt = f"""You are a compensation expert. Estimate salaries and return ONLY valid JSON:
{{
  "estimates": [
    {{
      "country": "India",
      "currency": "INR",
      "min_salary": 400000,
      "avg_salary": 700000,
      "max_salary": 1200000,
      "min_usd": 4800,
      "avg_usd": 8400,
      "max_usd": 14400,
      "market_note": "Brief note about this market",
      "top_cities": ["Bangalore", "Hyderabad", "Mumbai"],
      "top_companies": ["TCS", "Infosys", "Wipro", "Amazon"]
    }}
  ],
  "factors_that_increase_salary": ["factor1", "factor2", "factor3"],
  "negotiation_tips": ["tip1", "tip2", "tip3"],
  "certifications_for_higher_pay": ["cert1", "cert2"],
  "career_progression": {{
    "current": "{experience}",
    "next_role": "Senior Data Analyst",
    "timeline": "2-3 years",
    "salary_jump": "30-50% increase"
  }},
  "remote_salary_note": "Note about remote work impact on salary"
}}

Role: {role}
Experience: {experience}
Skills: {skills or 'Not specified'}

Economic Context:
{country_context}

Provide realistic salary estimates in local currency AND USD equivalent."""

            try:
                # Try models in order with automatic fallback
                models_to_try = [
                    ("llama-3.3-70b-versatile", 2000),
                    ("openai/gpt-oss-120b", 2000),
                    ("llama-3.1-8b-instant", 2000)
                ]
                
                result = None
                last_error = None
                for model, max_tokens in models_to_try:
                    try:
                        result = groq_json(prompt, model=model, max_tokens=max_tokens)
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
                    _render_salary(result, display_currency, role, experience)
                else:
                    if last_error:
                        error_str = str(last_error)
                        if "rate_limit" in error_str.lower() or "limit" in error_str.lower():
                            st.error("⏳ **API limit exhausted for today.** All models have reached their daily token limit. Please try again tomorrow!")
                        else:
                            st.error(f"❌ Estimation failed: {error_str[:100]}... Please try again.")
                    else:
                        st.error("❌ All models are currently at capacity. Please try again tomorrow!")
            except Exception as e:
                error_str = str(e)
                if "rate_limit" in error_str.lower() or "limit" in error_str.lower():
                    st.error("⏳ **API limit exhausted for today.** All models have reached their daily token limit. Please try again tomorrow!")
                else:
                    st.error(f"Estimation failed: {error_str}")


def _render_salary(result: dict, display_currency: str, role: str, experience: str):
    st.markdown("---")
    st.markdown(f"## 💰 Salary Estimates: {role} | {experience}")

    estimates = result.get("estimates", [])

    if estimates:
        # Bar chart comparison
        countries_list = [e["country"] for e in estimates]
        avg_usd = [e.get("avg_usd", 0) for e in estimates]
        min_usd = [e.get("min_usd", 0) for e in estimates]
        max_usd = [e.get("max_usd", 0) for e in estimates]

        fig = go.Figure()
        fig.add_trace(go.Bar(name='Minimum', x=countries_list, y=min_usd,
                             marker_color='#ef4444'))
        fig.add_trace(go.Bar(name='Average', x=countries_list, y=avg_usd,
                             marker_color='#3b82f6'))
        fig.add_trace(go.Bar(name='Maximum', x=countries_list, y=max_usd,
                             marker_color='#22c55e'))
        fig.update_layout(
            barmode='group',
            title='Salary Comparison (USD Equivalent)',
            plot_bgcolor='rgba(0,0,0,0)',
            paper_bgcolor='rgba(0,0,0,0)',
            font=dict(color='white'),
            yaxis_title='Annual Salary (USD)',
            height=400
        )
        st.plotly_chart(fig, use_container_width=True)

        # Country cards
        cols = st.columns(len(estimates))
        for i, est in enumerate(estimates):
            with cols[i]:
                st.markdown(f"""
                <div style="background:#1e3a4a;border-radius:12px;padding:1.2rem;text-align:center;">
                <h3 style="color:#87ceeb;margin:0;">{est['country']}</h3>
                <p style="color:#aaa;font-size:0.8rem;margin:4px 0;">{est.get('currency','')}</p>
                <p style="color:#22c55e;font-size:1.5rem;font-weight:800;margin:8px 0;">
                  {est.get('avg_salary', 0):,}</p>
                <p style="color:#aaa;font-size:0.75rem;">
                  Min: {est.get('min_salary',0):,} | Max: {est.get('max_salary',0):,}</p>
                <p style="color:#87ceeb;font-size:0.75rem;margin-top:8px;">{est.get('market_note','')}</p>
                </div>
                """, unsafe_allow_html=True)

            st.markdown("")
            if est.get("top_cities"):
                st.markdown(f"**Top Cities:** {', '.join(est.get('top_cities',[]))}")
            if est.get("top_companies"):
                st.markdown(f"**Top Employers:** {', '.join(est.get('top_companies',[]))}")

    st.markdown("---")
    col_a, col_b = st.columns(2)

    with col_a:
        factors = result.get("factors_that_increase_salary", [])
        if factors:
            st.markdown("### 📈 Factors That Increase Your Salary")
            for f in factors:
                st.success(f"✅ {f}")

        certs = result.get("certifications_for_higher_pay", [])
        if certs:
            st.markdown("### 📜 Certifications for Higher Pay")
            for c in certs:
                st.info(f"🏆 {c}")

    with col_b:
        tips = result.get("negotiation_tips", [])
        if tips:
            st.markdown("### 💬 Salary Negotiation Tips")
            for t in tips:
                st.markdown(f"→ {t}")

        prog = result.get("career_progression", {})
        if prog:
            st.markdown("### 🚀 Career Progression")
            st.markdown(f"""
            <div style="background:#1e3a4a;border-radius:8px;padding:1rem;">
            <p><strong>Next Role:</strong> {prog.get('next_role','')}</p>
            <p><strong>Timeline:</strong> {prog.get('timeline','')}</p>
            <p><strong>Expected Salary Jump:</strong> <span style="color:#22c55e;">{prog.get('salary_jump','')}</span></p>
            </div>
            """, unsafe_allow_html=True)

    if result.get("remote_salary_note"):
        st.info(f"🌐 **Remote Work Impact:** {result['remote_salary_note']}")
