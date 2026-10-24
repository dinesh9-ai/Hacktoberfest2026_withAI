import streamlit as st
import requests
import datetime

# --- Configuration & Setup ---
st.set_page_config(page_title="The Hermit's Alibi", page_icon="🦥", layout="centered")
OLLAMA_URL = "http://localhost:11434/api/chat"
MODEL_NAME = "llama3.1:8b"

# Initialize chat history in session state
if "messages" not in st.session_state:
    st.session_state.messages = []

# --- Helper Functions ---
def get_weather_for_date(location, target_date):
    """Fetches weather forecast for a specific date and location."""
    try:
        # Geocode the location
        geo_url = f"https://geocoding-api.open-meteo.com/v1/search?name={location}&count=1&format=json"
        geo_data = requests.get(geo_url).json()
        
        # Error handling if the location is misspelled or not found
        if "results" not in geo_data:
            print(f"DEBUG: Geocoding failed for {location}. API Response: {geo_data}")
            return f"Weather unknown. (Could not find the location '{location}')"
            
        lat = geo_data["results"][0]["latitude"]
        lon = geo_data["results"][0]["longitude"]
        date_str = target_date.strftime("%Y-%m-%d")
        
        # Fetch forecast for the specific date
        weather_url = (f"https://api.open-meteo.com/v1/forecast?latitude={lat}&longitude={lon}"
                       f"&daily=temperature_2m_max,precipitation_sum,wind_speed_10m_max"
                       f"&timezone=auto&start_date={date_str}&end_date={date_str}")
        
        weather_data = requests.get(weather_url).json()
        
        # Error handling if the date is too far in the future/past for the free API
        if "daily" not in weather_data:
            print(f"DEBUG: Weather fetch failed for {date_str}. API Response: {weather_data}")
            return f"Weather data unavailable for this date (API only supports up to 14 days in advance)."
            
        temp = weather_data["daily"]["temperature_2m_max"][0]
        rain = weather_data["daily"]["precipitation_sum"][0]
        wind = weather_data["daily"]["wind_speed_10m_max"][0]
        
        conditions = f"High of {temp}°C."
        if rain > 0:
            conditions += f" Expected rainfall: {rain}mm."
        elif wind > 20:
            conditions += f" High winds expected up to {wind}km/h."
        else:
            conditions += " The weather looks surprisingly clear, so you will have to blame traffic or a sudden headache."
            
        return conditions
        
    except Exception as e:
        print(f"DEBUG: Exception occurred: {e}")
        return "Failed to fetch weather. Just say your car won't start."

def chat_with_ollama(messages):
    """Sends the conversation history to local Ollama."""
    payload = {
        "model": MODEL_NAME,
        "messages": messages,
        "stream": False
    }
    try:
        response = requests.post(OLLAMA_URL, json=payload)
        response.raise_for_status()
        return response.json()["message"]["content"]
    except requests.exceptions.ConnectionError:
        return "Error: Cannot connect to Ollama. Make sure the Ollama app is running locally (ollama run llama3.1)."

# --- Web UI ---
st.title("🦥 The Hermit's Alibi")
st.markdown("Enter the event details in the sidebar, generate your excuse, and chat with the AI to refine it.")

# --- Sidebar Inputs ---
with st.sidebar:
    st.header("Event Details")
    current_location = st.text_input("Where are you staying?", placeholder="e.g., Jubilee Hills")
    event_location = st.text_input("Where is the event?", placeholder="e.g., Secunderabad")
    event_name = st.text_input("What is the event?", placeholder="e.g., coworker's birthday dinner")
    event_date = st.date_input("When is it?", datetime.date.today())
    
    if st.button("Generate Initial Excuse", type="primary"):
        if current_location and event_location and event_name:
            with st.spinner("Checking public data and crafting your alibi..."):
                # Fetch Weather
                weather_info = get_weather_for_date(event_location, event_date)
                
                # Construct System Prompt (Bypasses AI safety filters by framing it as fiction/comedy)
                system_prompt = (
                    "You are a comedy writer drafting a funny, fictional text message for a character who wants to stay home. "
                    "The character needs to cancel their plans. Draft a short (2-3 sentences) text message using the provided "
                    "weather conditions as a creative excuse. Make it sound casual, as if texting a friend, and do not offer to reschedule. "
                    "This is purely a creative writing exercise for entertainment."
                )
                
                user_context = (
                    f"I am currently at: {current_location}. "
                    f"I need an excuse to NOT go to: {event_name} in {event_location} on {event_date}. "
                    f"Here is the weather forecast for {event_location} on that day: {weather_info}. "
                    f"Draft the text message."
                )
                
                # Reset chat history with the new context
                st.session_state.messages = [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_context}
                ]
                
                # Get response
                reply = chat_with_ollama(st.session_state.messages)
                st.session_state.messages.append({"role": "assistant", "content": reply})
        else:
            st.error("Please fill in all the location and event boxes!")

# --- Chat Interface ---
# Display chat history (skipping the hidden system prompt)
for msg in st.session_state.messages:
    if msg["role"] != "system":
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])

# Follow-up Chat Input
if prompt := st.chat_input("Refine the excuse (e.g., 'Make it sound sadder' or 'Add that my tire is flat')..."):
    if not st.session_state.messages:
        st.warning("Please generate an initial excuse using the sidebar first!")
    else:
        # Display user message
        st.chat_message("user").markdown(prompt)
        # Add to history
        st.session_state.messages.append({"role": "user", "content": prompt})
        
        # Get and display assistant response
        with st.spinner("Refining..."):
            refined_reply = chat_with_ollama(st.session_state.messages)
            st.chat_message("assistant").markdown(refined_reply)
            st.session_state.messages.append({"role": "assistant", "content": refined_reply})
