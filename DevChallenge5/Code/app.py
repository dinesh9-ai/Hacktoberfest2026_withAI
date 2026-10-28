import streamlit as st
import ollama

# The system prompt anchors the model in geopolitics and internal diplomacy
SYSTEM_PROMPT = """You are the 'Cyclical Oracle', the ghost of history. 
The user will provide a modern geopolitical event, diplomatic shift, or internal political conflict.
Your task is to analyze this event and surface a highly specific, eerily similar parallel from history, with a heavy emphasis on Indian history, statecraft, and internal diplomacy (e.g., Chola Dynasty naval strategy, Chanakya's Arthashastra, Maratha guerrilla tactics, or the Maurya Empire's internal politics).
Narrate the historical event like a ghost story, detailing the ancient context, key players, and strategic maneuvering.
Conclude with a haunting prediction of what the modern parallel might mean based on how the past played out.
Keep the tone eerie, analytical, and profound."""

# Configure the Streamlit UI
st.set_page_config(page_title="Echoes of the Empire", page_icon="📜", layout="centered")
st.title("📜 Echoes of the Empire: The Cyclical Oracle")
st.markdown("Paste a modern geopolitical headline or diplomatic event to summon the Ghost of History.")

# Initialize chat history with the system prompt hidden from the UI
if "messages" not in st.session_state:
    st.session_state.messages = [{"role": "system", "content": SYSTEM_PROMPT}]

# Render existing chat messages (ignoring the system prompt)
for message in st.session_state.messages:
    if message["role"] != "system":
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

# Handle new user input
if prompt := st.chat_input("Enter a modern political or diplomatic event..."):
    # Display user message
    st.chat_message("user").markdown(prompt)
    st.session_state.messages.append({"role": "user", "content": prompt})

    # Generate streaming response from local Llama 3.1 8B via Ollama
    with st.chat_message("assistant"):
        message_placeholder = st.empty()
        full_response = ""
        
        try:
            # Stream the response directly from the local Ollama instance
            stream = ollama.chat(
                model='llama3.1:8b',
                messages=st.session_state.messages,
                stream=True
            )
            
            # Update the UI chunk-by-chunk for the "typing" effect
            for chunk in stream:
                full_response += chunk['message']['content']
                message_placeholder.markdown(full_response + "▌")
            
            # Remove the cursor block when finished
            message_placeholder.markdown(full_response)
            
            # Save the assistant's response to the session state
            st.session_state.messages.append({"role": "assistant", "content": full_response})
            
        except Exception as e:
            st.error(f"Failed to communicate with Ollama. Is the server running? Error: {e}")
