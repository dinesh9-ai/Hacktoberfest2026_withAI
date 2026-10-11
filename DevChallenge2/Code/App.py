import streamlit as st
import pandas as pd
import numpy as np
import ollama
import glob
import os

# --- Page Configuration ---
st.set_page_config(page_title="OpenStride Coach", page_icon="🏃‍♂️", layout="wide")
st.title("🏃‍♂️ OpenStride: Offline AI Coach")

# --- Helper Function: Process Run Data ---
def analyze_run(file_path):
    df = pd.read_csv(file_path)
    # Calculate impact magnitude
    df['Impact_Magnitude'] = np.sqrt(df['Accel_X']**2 + df['Accel_Y']**2 + df['Accel_Z']**2)
    duration_mins = round((len(df) * 0.1) / 60, 1) # Assuming 10Hz log rate
    avg_impact = round(df['Impact_Magnitude'].mean(), 2)
    
    # Calculate fatigue (comparing 2nd half of run to 1st half)
    if len(df) > 10:
        halfway = len(df) // 2
        fatigue_ratio = df['Impact_Magnitude'].iloc[halfway:].mean() / df['Impact_Magnitude'].iloc[:halfway].mean()
    else:
        fatigue_ratio = 1.0
        
    return duration_mins, avg_impact, fatigue_ratio

# --- Data Loading ---
LOG_DIR = "logs"
if not os.path.exists(LOG_DIR):
    os.makedirs(LOG_DIR)

all_files = glob.glob(os.path.join(LOG_DIR, "*.csv"))

if not all_files:
    st.warning(f"No run logs found. Please drop your CSV files into the '{LOG_DIR}' folder.")
    st.stop()

# Sort files by modification time (latest last)
all_files.sort(key=os.path.getmtime)
latest_file = all_files[-1]
history_files = all_files[:-1]

# Process latest run
latest_duration, latest_impact, latest_fatigue = analyze_run(latest_file)
fatigue_status = "Increased (Leg Fatigue)" if latest_fatigue > 1.05 else "Stable (Good Endurance)"

# --- Sidebar: Hardware Data Dashboard ---
with st.sidebar:
    st.header("📊 Today's Hardware Data")
    st.metric(label="Run Duration", value=f"{latest_duration} mins")
    st.metric(label="Average Impact Force", value=f"{latest_impact} m/s²")
    st.metric(label="Form/Fatigue Status", value=fatigue_status)
    
    st.divider()
    
    st.header("📚 Historical Records")
    if history_files:
        st.write(f"**{len(history_files)} past runs detected.**")
        hist_data = []
        for i, f in enumerate(history_files):
            d_mins, imp, _ = analyze_run(f)
            hist_data.append({"Run": f"Run {i+1}", "Duration (m)": d_mins, "Impact": imp})
        
        hist_df = pd.DataFrame(hist_data)
        st.dataframe(hist_df, hide_index=True, use_container_width=True)
        
        # Simple trend chart for historical impact force
        st.write("**Impact Force Trend:**")
        st.line_chart(hist_df.set_index("Run")["Impact"])
        
        history_summary = f"User has {len(history_files)} past runs. Average historical duration: {round(hist_df['Duration (m)'].mean(),1)} mins. Average historical impact: {round(hist_df['Impact'].mean(),2)} m/s²."
    else:
        st.info("No historical data available. This is your first logged run!")
        history_summary = "No historical data available. This is the user's first logged run."

# --- Main Interface: LLM Chat ---
st.subheader("🤖 Consult Your Coach")

# Initialize chat history in Streamlit session state
if "messages" not in st.session_state:
    st.session_state.messages = []
    st.session_state.coach_initialized = False

# Form to get user context before first AI generation
if not st.session_state.coach_initialized:
    with st.form("init_form"):
        st.write("Before we generate tomorrow's plan, tell me about today:")
        user_goal = st.text_input("Current Training Goal (e.g., Sub 4-hour marathon):")
        user_feedback = st.text_input("How did your body feel? (e.g., Left calf was tight):")
        submitted = st.form_submit_button("Generate Plan")
        
        if submitted and user_goal and user_feedback:
            # Construct the hidden system prompt
            system_prompt = f"""
            You are an elite marathon coach running locally.
            
            HISTORICAL BASELINE:
            {history_summary}
            
            TODAY'S RUN DATA:
            - Duration: {latest_duration} minutes
            - Average Impact Force: {latest_impact} m/s^2
            - Form breakdown: {fatigue_status}
            
            USER'S PERSONAL INPUT:
            - Goal: {user_goal}
            - Post-run feeling: {user_feedback}
            
            First, provide a brief analysis comparing today to their history. Then, give a specific plan for tomorrow. 
            Keep your answers concise, formatting with bold text and bullet points where appropriate.
            """
            
            # Save system prompt to history (hidden from UI)
            st.session_state.messages.append({"role": "system", "content": system_prompt})
            st.session_state.coach_initialized = True
            st.rerun()

# --- Chat UI ---
if st.session_state.coach_initialized:
    # Display chat messages (skipping the hidden system prompt)
    for message in st.session_state.messages:
        if message["role"] != "system":
            with st.chat_message(message["role"]):
                st.markdown(message["content"])

    # If it's the very first time initializing, auto-trigger the coach's first response
    if len(st.session_state.messages) == 1:
        with st.chat_message("assistant"):
            with st.spinner("Analyzing kinematics and generating plan..."):
                response = ollama.chat(model='llama3.1:8b', messages=st.session_state.messages)
                msg = response['message']['content']
                st.markdown(msg)
                st.session_state.messages.append({"role": "assistant", "content": msg})

    # Accept continuous user input for follow-up questions
    if prompt := st.chat_input("Ask a follow-up or tweak the plan..."):
        # Add user message to chat history
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)

        # Generate LLM response
        with st.chat_message("assistant"):
            with st.spinner("Thinking..."):
                response = ollama.chat(model='gemma2', messages=st.session_state.messages)
                msg = response['message']['content']
                st.markdown(msg)
                st.session_state.messages.append({"role": "assistant", "content": msg})
