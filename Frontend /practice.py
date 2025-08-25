import streamlit as st 
import os 
import sys 

# to find the backend path and to connect to the backend 
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
search_engine_dir = os.path.join(parent_dir, 'Search_Engine')
sys.path.insert(0, search_engine_dir)

from RAG import search, build_prompt, lamma3_groq, rag_pipeline
collection_name = "reddit_post_comment"


# Create a title 
st.title('All About Reddit')

# Create the chat box first message 
# make sure all messages are remembered in the session state 
if "messages" not in st.session_state:
    st.session_state.messages = [
        {'role':'bot',
         'content':'I am your Reddit expert! Ask me anything about Reddit post! 👋'
        }
    ] 

# to create the chat container that have conbtinuous chat 
# each interaction (e.g. press button) rerun the entire page from beginning to end, so must use for loop to retrieve saved conversation to display, else it will be gone when the next message comes in 
for message in st.session_state.messages:
    role = message['role']
    content = message['content']

    if role == "user":
        st.markdown(f"""
        <div style="background-color: white; padding: 10px; border-radius: 10px; 
                    margin: 10px 0; text-align: right;">
            <strong>You:</strong><br>{content}
        </div>
        """, unsafe_allow_html=True)
    else:
        st.markdown(f"""
        <div style="background-color: #F1F1F1; padding: 10px; border-radius: 10px; 
                    margin: 10px 0;">
            <strong>🤖 Bot:</strong><br>{content}
        </div>
        """, unsafe_allow_html=True)

# for user to type in their question: 
user_message = st.chat_input("Ask Something:")

if user_message:
    # append the user message to session state 
    st.session_state.messages.append(
        {
            'role':'user',
            'content':user_message
        }
    )
    with st.spinner("🤔 Thinking..."):
        bot_reply = rag_pipeline(user_message,collection_name)

    st.session_state.messages.append(
        {
            'role':'bot',
            'content':bot_reply
        }
    )

    st.rerun() # to trigger the display of new message 



# Create a side bar 
with st.sidebar: 
    if st.button("🗑️ Clear Chat Hitory"): 
        # keep the init message 
        st.session_state.messages = st.session_state.messages[:1]
        # reset chat 
        st.rerun() 
