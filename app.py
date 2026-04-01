import streamlit as st
import pandas as pd
import os
import gspread
from google.oauth2.service_account import Credentials
from dotenv import load_dotenv
from streamlit_mic_recorder import speech_to_text
from streamlit_geolocation import streamlit_geolocation
from geopy.distance import geodesic
import pydeck as pdk
from agent import get_gas_info_response

load_dotenv()


SHEET_KEY = os.getenv("SHEET_KEY") or st.secrets.get("SHEET_KEY")

st.set_page_config(page_title="Gas Availability AI Agent", page_icon="⛽", layout="wide")

env_api_key = os.getenv("GROQ_API_KEY") or st.secrets.get("GROQ_API_KEY")
api_key = env_api_key if env_api_key and env_api_key != "YOUR_GROQ_API_KEY_HERE" else None

if not api_key:
    st.error("⚠️ **Groq API Key is missing!** Please add it to your .env file or Streamlit Secrets.")
    st.stop()

def fetch_gas_data_from_gsheets():
    """Fetches real-time gas data from Google Sheets using Service Account."""
    scope = ["https://www.googleapis.com/auth/spreadsheets.readonly"]
    try:
        if "google_credentials" in st.secrets:
            creds_dict = dict(st.secrets["google_credentials"])
            creds = Credentials.from_service_account_info(creds_dict, scopes=scope)
        elif os.path.exists("credentials.json"):
            creds = Credentials.from_service_account_file("credentials.json", scopes=scope)
        else:
            raise FileNotFoundError("Google Credentials not found in secrets or locally.")

        client = gspread.authorize(creds)
        sheet = client.open_by_key(SHEET_KEY).sheet1
        data = sheet.get_all_records()
        return pd.DataFrame(data)
    except Exception as e:
        st.error(f"Failed to fetch data from Google Sheets: {e}")
        if os.path.exists("Gas Availability - Sheet1.csv"):
            return pd.read_csv("Gas Availability - Sheet1.csv")
        return None

def calculate_distances(df, user_lat, user_lon):
    """Calculates distance between user and each gas agency."""
    def get_distance(row):
        try:
            agency_coords = (float(row['latitude']), float(row['longitude']))
            user_coords = (user_lat, user_lon)
            return round(geodesic(user_coords, agency_coords).km, 2)
        except (ValueError, TypeError):
            return 99999.0
    
    df['distance'] = df.apply(get_distance, axis=1)
    return df


st.title("⛽ Gas Availability AI Agent (Real-time GPS)")

if "messages" not in st.session_state:
    st.session_state.messages = []
with st.sidebar:
    st.header("📍 Your Location")
    st.write("Click the button below to share your GPS location:")
    location = streamlit_geolocation()
    
    user_lat = location.get("latitude")
    user_lon = location.get("longitude")
    
    if user_lat and user_lon:
        st.success(f"GPS Active: {user_lat:.4f}, {user_lon:.4f}")
    else:
        st.warning("GPS not shared yet. Please click the button.")

    st.write("---")
    st.write("🎤 **Voice Search:**")
    voice_prompt = speech_to_text(
        language='en', 
        start_prompt="Click to speak", 
        stop_prompt="Stop recording", 
        just_once=True, 
        key='STT'
    )

with st.container():
    query = st.chat_input("Ask a specific question (e.g., 'Is HP gas available within 3km?')")

if "last_voice_prompt" not in st.session_state:
    st.session_state.last_voice_prompt = None

triggered_query = None
if voice_prompt and voice_prompt != st.session_state.last_voice_prompt:
    triggered_query = voice_prompt
    st.session_state.last_voice_prompt = voice_prompt
elif query:
    triggered_query = query

if triggered_query:
    if user_lat and user_lon:
        with st.status("Fetching nearby gas agencies...", expanded=True) as status:
            df = fetch_gas_data_from_gsheets()
            
            if df is not None:
                df = calculate_distances(df, user_lat, user_lon)
                
                nearby_df = df.sort_values(by='distance').head(3)
                
                status.update(label="Data fetched and distances calculated!", state="complete")
                
                st.subheader("🗺️ 3 Nearest Gas Agencies")
                
                agency_layer = pdk.Layer(
                    "ScatterplotLayer",
                    nearby_df,
                    get_position=["longitude", "latitude"],
                    get_color="[0, 200, 0, 160]", 
                    get_radius=150,
                    pickable=True,
                )
                
                user_layer = pdk.Layer(
                    "ScatterplotLayer",
                    pd.DataFrame([{"latitude": user_lat, "longitude": user_lon}]),
                    get_position=["longitude", "latitude"],
                    get_color="[255, 0, 0, 200]", 
                    get_radius=200,
                )
                
                view_state = pdk.ViewState(
                    latitude=user_lat,
                    longitude=user_lon,
                    zoom=13,
                    pitch=0,
                )
                
                st.pydeck_chart(pdk.Deck(
                    layers=[agency_layer, user_layer],
                    initial_view_state=view_state,
                    tooltip={"text": "{name}\nDistance: {distance} km\nStatus: {availability}"}
                ))
                
                st.subheader("📋 Top 3 Nearby Agencies")
                st.dataframe(nearby_df[['name', 'distance', 'availability', 'phone']].rename(columns={
                    'name': 'Agency Name',
                    'distance': 'Distance (km)',
                    'availability': 'Status',
                    'phone': 'Phone'
                }))

                with st.chat_message("user"):
                    st.markdown(triggered_query)
                with st.chat_message("assistant"):
                    try:
                        response = get_gas_info_response(nearby_df, triggered_query, api_key)
                        st.markdown(response)
                    except Exception as agent_error:
                        st.error(f"Agent Error: {agent_error}")
                        st.info("I found these agencies nearby, but I had trouble processing your specific question.")
            else:
                st.error("Could not load gas agency data.")
                status.update(label="Failed to fetch data.", state="error")
    else:
        with st.chat_message("user"):
            st.markdown(triggered_query)
        with st.chat_message("assistant"):
            st.warning("📍 **Location required!** Please click the **'Share Location'** button in the sidebar before I can find nearest gas agencies for you.")
else:
    if not (user_lat and user_lon):
        st.info("👈 Please enable your GPS location in the sidebar and then ask a question to find nearby agencies.")
    else:
        st.success("✅ GPS Active. Ready for your query!")
