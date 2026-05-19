import os, json, time, logging
from groq import Groq
import streamlit as st

def get_groq_clients():
    """Get list of Groq clients from multiple API keys (comma-separated in env)"""
    api_keys_str = os.getenv("GROQ_API_KEYS", os.getenv("GROQ_API_KEY", ""))
    if not api_keys_str:
        raise ValueError("GROQ_API_KEY or GROQ_API_KEYS not found in environment")
    
    # Support both single key (GROQ_API_KEY) and multiple keys (GROQ_API_KEYS=key1,key2,key3)
    api_keys = [k.strip() for k in api_keys_str.split(",") if k.strip()]
    return [Groq(api_key=key) for key in api_keys], len(api_keys)

@st.cache_resource
def _get_client_index():
    """Track which API key to use next (round-robin)"""
    return {"index": 0}

def get_next_groq_client():
    """Get next Groq client in round-robin fashion for load balancing"""
    clients, count = get_groq_clients()
    state = _get_client_index()
    client = clients[state["index"] % count]
    state["index"] = (state["index"] + 1) % count
    return client, state["index"] % count + 1

def groq_json(prompt: str, model: str = "llama-3.3-70b-versatile", max_tokens: int = 2000, retries: int = 3) -> dict:
    clients, total_clients = get_groq_clients()
    
    # Try each API key before giving up
    for key_attempt in range(total_clients):
        for attempt in range(retries):
            try:
                # Get next client in round-robin
                client, client_num = get_next_groq_client()
                
                raw = ""
                status_placeholder = st.empty()
                with status_placeholder.container():
                    with st.spinner(f"🔄 Generating with {model} (Key {client_num}/{total_clients})..."):
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
                error_str = str(e).lower()
                status_placeholder.empty()
                
                # If rate limit, try next API key
                if "rate_limit" in error_str or "429" in error_str or "limit" in error_str:
                    logging.warning(f"Rate limit on key {client_num}, trying next key...")
                    break  # Try next API key
                
                # Retry same key on other errors
                if attempt < retries - 1:
                    time.sleep(1)
                else:
                    logging.error(f"Groq JSON error on key {client_num}: {e}")
    
    raise Exception(f"Failed on all {total_clients} API keys")

def groq_text(prompt: str, model: str = "llama-3.3-70b-versatile", max_tokens: int = 2000, retries: int = 3) -> str:
    clients, total_clients = get_groq_clients()
    
    # Try each API key before giving up
    for key_attempt in range(total_clients):
        for attempt in range(retries):
            try:
                # Get next client in round-robin
                client, client_num = get_next_groq_client()
                
                raw = ""
                status_placeholder = st.empty()
                with status_placeholder.container():
                    with st.spinner(f"🔄 Generating with {model} (Key {client_num}/{total_clients})..."):
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
                error_str = str(e).lower()
                status_placeholder.empty()
                
                # If rate limit, try next API key
                if "rate_limit" in error_str or "429" in error_str or "limit" in error_str:
                    logging.warning(f"Rate limit on key {client_num}, trying next key...")
                    break  # Try next API key
                
                # Retry same key on other errors
                if attempt < retries - 1:
                    time.sleep(1)
                else:
                    logging.error(f"Groq text error on key {client_num}: {e}")
    
    raise Exception(f"Failed on all {total_clients} API keys")
