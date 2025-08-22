# learning line by line to understand what happen 
import streamlit as st 
import pandas as pd 
import numpy as np 
from datetime import datetime

st.set_page_config(
        page_title="My RAG Chat",      # Browser tab title
        page_icon="🤖",                # Browser tab icon
        layout="wide"                  # Use full width instead of centered
    )

st.title("🤖 My First RAG Chat App")

st.write("This is my learning project!")

user_name = st.text_input("What's your name?")

if user_name:
        st.write(f"Hello, {user_name}! 👋")

if "counter" not in st.session_state:  # remember the counter state
        st.session_state.counter = 0
st.write(f"Counter: {st.session_state.counter}")

col1, col2, col3 = st.columns(3)
with col1:
    if st.button("Add 1"):
        st.session_state.counter += 1
        # Script will rerun, but counter value is remembered!

with col2:
    if st.button("Subtract 1"):
        st.session_state.counter -= 1

with col3:
    if st.button("Reset"):
        st.session_state.counter = 0

st.write("Try clicking buttons - notice how the value persists!")

st.title("💬 Message System")
if "messages" not in st.session_state:
        st.session_state.messages = []

st.subheader("Chat History:")
for i, message in enumerate(st.session_state.messages):
        st.write(f"{i+1}. **{message['role']}**: {message['content']}")

# user input 
new_message = st.text_input("Type a message:")
col1, col2 = st.columns(2)
    
with col1:
    if st.button("Send as User") and new_message:
        st.session_state.messages.append({
            "role": "User",
            "content": new_message,
            "timestamp": datetime.now()
        })
        # Clear the input by rerunning
        st.rerun()

with col2:
    if st.button("Send as Bot") and new_message:
        st.session_state.messages.append({
            "role": "Bot", 
            "content": new_message,
            "timestamp": datetime.now()
        })
        st.rerun()

if st.button("Clear All Messages"):
        st.session_state.messages = []
        st.rerun()

st.markdown("""
<style>
.user-message {
    background-color: #DCF8C6;
    padding: 10px;
    border-radius: 10px;
    margin: 10px 0;
    text-align: right;
}

.bot-message {
    background-color: #F1F1F1;
    padding: 10px;
    border-radius: 10px;
    margin: 10px 0;
    text-align: left;
}

.chat-container {
    max-height: 400px;
    overflow-y: auto;
    border: 1px solid #ddd;
    padding: 10px;
    border-radius: 10px;
}
</style>
""", unsafe_allow_html=True)

st.title("🎨 Styled Chat")

# Initialize messages
if "styled_messages" not in st.session_state:
    st.session_state.styled_messages = [
        {"role": "bot", "content": "Hello! I'm your assistant."}
    ]

# Display messages with custom styling
st.markdown('<div class="chat-container">', unsafe_allow_html=True)

for message in st.session_state.styled_messages:
        if message["role"] == "user":
            st.markdown(f"""
            <div class="user-message">
                <strong>You:</strong> {message["content"]}
            </div>
            """, unsafe_allow_html=True)
        # following css format defined above 
        else:
            st.markdown(f"""
            <div class="bot-message"> 
                <strong>Bot:</strong> {message["content"]}
            </div>
            """, unsafe_allow_html=True)
    
st.markdown('</div>', unsafe_allow_html=True)

 # Input
user_input = st.text_input("Your message:", key="styled_input") # input bar 

if st.button("Send", key="styled_send") and user_input:
    # Add user message
    st.session_state.styled_messages.append({ #
        "role": "user", 
        "content": user_input
    })
    
    # Add bot response (mock)
    st.session_state.styled_messages.append({
        "role": "bot",
        "content": f"I received: '{user_input}'. This is a mock response!"
    })
    
    st.rerun()


with st.sidebar:
    st.header("Settings")
    
    # Various input widgets
    search_limit = st.slider("Search Results:", 1, 10, 5)
    api_provider = st.selectbox("API Provider:", ["groq", "openai", "anthropic"])
    enable_sources = st.checkbox("Show Sources", value=True)
    
    st.header("Actions")
    if st.button("Clear Chat", key="sidebar_clear"):
        st.session_state.main_messages = []
        st.rerun()
# Main content area
st.write(f"Current settings:")
st.write(f"- Search Limit: {search_limit}")
st.write(f"- API Provider: {api_provider}")
st.write(f"- Show Sources: {enable_sources}")

# Initialize messages for this step
if "main_messages" not in st.session_state:
    st.session_state.main_messages = []


