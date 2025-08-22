# learning line by line to understand what happen 
import streamlit as st 
import pandas as pd 
import numpy as np 
from datetime import datetime
import os 
import sys 

current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
search_engine_dir = os.path.join(parent_dir, 'Search_Engine')
sys.path.insert(0, search_engine_dir)

from RAG import search, build_prompt, lamma3_groq, rag_pipeline

st.set_page_config(
    page_title="Simple RAG Chat",
    page_icon="🤖",
    layout="wide"
)

# Title
st.title("🤖 All About Reddit")
st.write("Ask me questions about Reddit discussions!")

# Initialize session state
if "chat_messages" not in st.session_state:
    st.session_state.chat_messages = [
        {
            "role": "assistant",
            "content": "Hi! I can help you find information from Reddit. What would you like to know?",
            "timestamp": datetime.now()
        }
    ]

# Sidebar settings
with st.sidebar:
    st.header("⚙️ Settings")
    
    if st.button("🗑️ Clear Chat"):
        st.session_state.chat_messages = st.session_state.chat_messages[:1]  # Keep welcome message
        st.rerun()

# Chat display area
chat_container = st.container()

with chat_container:
    for message in st.session_state.chat_messages:
        role = message["role"]
        content = message["content"]
        timestamp = message["timestamp"].strftime("%H:%M")
        
        if role == "user":
            st.markdown(f"""
            <div style="background-color: #DCF8C6; padding: 10px; border-radius: 10px; 
                        margin: 10px 0; text-align: right;">
                <strong>You ({timestamp}):</strong><br>{content}
            </div>
            """, unsafe_allow_html=True)
        else:
            st.markdown(f"""
            <div style="background-color: #F1F1F1; padding: 10px; border-radius: 10px; 
                        margin: 10px 0;">
                <strong>🤖 Assistant ({timestamp}):</strong><br>{content}
            </div>
            """, unsafe_allow_html=True)

# User input
user_input = st.chat_input("Ask me anything about Reddit discussions...")

if user_input:
    # Add user message

    st.session_state.chat_messages.append({
        "role": "user",
        "content": user_input,
        "timestamp": datetime.now()
    })

    try:
        with st.spinner("🤔 Thinking..."):
            result = rag_pipeline(user_input) 
        
        st.session_state.chat_messages.append({
            "role": "assistant", 
            "content": result,
            "timestamp": datetime.now()
        })
    except Exception as e:
        st.error(f"Error: {e}")
    
    st.rerun()

    


