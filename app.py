import streamlit as st
from agent import get_pandas_agent
import pandas as pd
import os
from dotenv import load_dotenv

from streamlit_mic_recorder import speech_to_text

load_dotenv()

st.set_page_config(page_title="Dynamic Gas Availability AI", page_icon="⛽", layout="wide")
env_api_key = os.getenv("GROQ_API_KEY")
api_key = env_api_key if env_api_key and env_api_key != "YOUR_GROQ_API_KEY_HERE" else None

st.title("⛽Gas Availability AI")
st.markdown("""
This agent provides real-time answers about gas cylinder availability based on the local data.
""")

if not api_key:
    st.error("⚠️ **Groq API Key is missing!**")
    st.stop()
if "messages" not in st.session_state:
    st.session_state.messages = []

for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

st.write("🎤 **Voice Search:**")
voice_prompt = speech_to_text(
    language='en', 
    start_prompt="Click to speak", 
    stop_prompt="Stop recording", 
    just_once=True, 
    key='STT'
)

prompt = st.chat_input("Ask about gas availability (e.g., 'Availability in Ameerpet' or 'Find HP gas near me')")


if voice_prompt:
    prompt = voice_prompt

if prompt:
    with st.chat_message("user"):
        st.markdown(prompt)
    st.session_state.messages.append({"role": "user", "content": prompt})

    try:
        with st.chat_message("assistant"):
            with st.spinner("Reading data and analyzing..."):
                csv_path = "Gas Availability - Sheet1.csv"
                if os.path.exists(csv_path):
                    df = pd.read_csv(csv_path)
                    agent = get_pandas_agent(df, api_key)
                    
                    response = agent.run(prompt)
                    st.markdown(response)
                    
                    if "latitude" in df.columns and "longitude" in df.columns:
                        with st.expander("📍 View Map of Agencies"):
                            st.map(df[['latitude', 'longitude']])
                            
                    st.session_state.messages.append({"role": "assistant", "content": response})
                else:
                    st.error(f"Error: {csv_path} not found.")
    except Exception as e:
        st.error(f"An error occurred: {str(e)}")




