import os, json, time, logging
from groq import Groq
import streamlit as st

def get_groq_client():
    """Get Groq client from single API key"""
    api_key = os.getenv("GROQ_API_KEY", "")
    if not api_key:
        raise ValueError("GROQ_API_KEY not found in environment")
    return Groq(api_key=api_key)

def groq_json(prompt: str, model: str = "llama-3.3-70b-versatile", max_tokens: int = 2000, retries: int = 3) -> dict:
    client = get_groq_client()
    for attempt in range(retries):
        try:
            raw = ""
            status_placeholder = st.empty()
            with status_placeholder.container():
                with st.spinner(f"🔄 Generating with {model}..."):
                    # Use streaming for real-time feedback
                    with client.chat.completions.create(
                        model=model,
                        messages=[{"role": "user", "content": prompt}],
                        temperature=0.3,
                        max_tokens=max_tokens,
                        stream=True,
                    ) as stream:
                        for text in stream.text_stream:
                            raw += text
            
            # Clean up markdown code blocks if present
            if raw.startswith("```"):
                raw = raw.split("```")[1]
                if raw.startswith("json"):
                    raw = raw[4:]
            if raw.endswith("```"):
                raw = raw[:-3]
            
            status_placeholder.empty()
            return json.loads(raw.strip())
        except Exception as e:
            if attempt < retries - 1:
                time.sleep(1)
            else:
                logging.error(f"Groq JSON error: {e}")
                raise

def groq_text(prompt: str, model: str = "llama-3.3-70b-versatile", max_tokens: int = 2000, retries: int = 3) -> str:
    client = get_groq_client()
    for attempt in range(retries):
        try:
            raw = ""
            status_placeholder = st.empty()
            with status_placeholder.container():
                with st.spinner(f"🔄 Generating with {model}..."):
                    # Use streaming for real-time feedback
                    with client.chat.completions.create(
                        model=model,
                        messages=[{"role": "user", "content": prompt}],
                        temperature=0.4,
                        max_tokens=max_tokens,
                        stream=True,
                    ) as stream:
                        for text in stream.text_stream:
                            raw += text
            
            status_placeholder.empty()
            return raw.strip()
        except Exception as e:
            if attempt < retries - 1:
                time.sleep(1)
            else:
                logging.error(f"Groq text error: {e}")
                raise
