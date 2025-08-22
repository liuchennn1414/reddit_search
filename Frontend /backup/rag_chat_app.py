import streamlit as st
from datetime import datetime
import uuid
import json

# =============================================================================
# CHAT HISTORY MANAGEMENT SYSTEM
# =============================================================================

class ChatManager:
    """Manages multiple chat sessions like Claude/ChatGPT"""
    
    def __init__(self):
        self.initialize_session_state()
    
    def initialize_session_state(self):
        """Initialize all session state variables"""
        
        # Current active chat ID
        if "current_chat_id" not in st.session_state:
            st.session_state.current_chat_id = None
        
        # Dictionary to store all chats {chat_id: chat_data}
        if "all_chats" not in st.session_state:
            st.session_state.all_chats = {}
        
        # Create first chat if none exists
        if not st.session_state.all_chats:
            self.create_new_chat()
    
    def create_new_chat(self):
        """Create a new chat session"""
        chat_id = str(uuid.uuid4())[:8]  # Short unique ID
        
        new_chat = {
            "id": chat_id,
            "title": "New Chat",  # Will be auto-generated from first message
            "created_at": datetime.now(),
            "updated_at": datetime.now(),
            "messages": [
                {
                    "role": "assistant",
                    "content": "👋 Hello! I'm your Reddit RAG Assistant. What would you like to know?",
                    "timestamp": datetime.now()
                }
            ]
        }
        
        # Add to all chats
        st.session_state.all_chats[chat_id] = new_chat
        
        # Set as current chat
        st.session_state.current_chat_id = chat_id
        
        return chat_id
    
    def get_current_chat(self):
        """Get the currently active chat"""
        if st.session_state.current_chat_id:
            return st.session_state.all_chats.get(st.session_state.current_chat_id)
        return None
    
    def switch_chat(self, chat_id):
        """Switch to a different chat"""
        if chat_id in st.session_state.all_chats:
            st.session_state.current_chat_id = chat_id
            st.rerun()
    
    def delete_chat(self, chat_id):
        """Delete a chat session"""
        if chat_id in st.session_state.all_chats:
            del st.session_state.all_chats[chat_id]
            
            # If we deleted the current chat, switch to another one or create new
            if st.session_state.current_chat_id == chat_id:
                if st.session_state.all_chats:
                    # Switch to the most recent chat
                    latest_chat = max(
                        st.session_state.all_chats.values(),
                        key=lambda x: x["updated_at"]
                    )
                    st.session_state.current_chat_id = latest_chat["id"]
                else:
                    # Create new chat if no chats left
                    self.create_new_chat()
            
            st.rerun()
    
    def add_message_to_current_chat(self, role, content):
        """Add a message to the current chat"""
        current_chat = self.get_current_chat()
        if current_chat:
            message = {
                "role": role,
                "content": content,
                "timestamp": datetime.now()
            }
            current_chat["messages"].append(message)
            current_chat["updated_at"] = datetime.now()
            
            # Auto-generate title from first user message
            if role == "user" and current_chat["title"] == "New Chat":
                # Use first 50 characters of the message as title
                title = content[:50].strip()
                if len(content) > 50:
                    title += "..."
                current_chat["title"] = title
    
    def get_chat_list_sorted(self):
        """Get all chats sorted by most recent first"""
        return sorted(
            st.session_state.all_chats.values(),
            key=lambda x: x["updated_at"],
            reverse=True
        )
    
    def export_chat_history(self):
        """Export all chats as JSON"""
        export_data = {
            "exported_at": datetime.now().isoformat(),
            "total_chats": len(st.session_state.all_chats),
            "chats": {}
        }
        
        for chat_id, chat in st.session_state.all_chats.items():
            export_data["chats"][chat_id] = {
                "title": chat["title"],
                "created_at": chat["created_at"].isoformat(),
                "updated_at": chat["updated_at"].isoformat(),
                "message_count": len(chat["messages"]),
                "messages": [
                    {
                        "role": msg["role"],
                        "content": msg["content"],
                        "timestamp": msg["timestamp"].isoformat()
                    }
                    for msg in chat["messages"]
                ]
            }
        
        return json.dumps(export_data, indent=2)

# =============================================================================
# SIDEBAR: CHAT HISTORY INTERFACE
# =============================================================================

def render_chat_sidebar(chat_manager):
    """Render the chat history sidebar like Claude/ChatGPT"""
    
    with st.sidebar:
        # Header with New Chat button
        st.markdown("### 💬 Chat History")
        
        # New Chat button (prominent)
        if st.button("➕ New Chat", use_container_width=True, type="primary"):
            chat_manager.create_new_chat()
            st.rerun()
        
        st.markdown("---")
        
        # Chat history list
        current_chat_id = st.session_state.current_chat_id
        chat_list = chat_manager.get_chat_list_sorted()
        
        if chat_list:
            st.markdown("#### Recent Chats")
            
            for chat in chat_list:
                chat_id = chat["id"]
                title = chat["title"]
                updated = chat["updated_at"]
                message_count = len(chat["messages"])
                
                # Create columns for chat item layout
                col1, col2 = st.columns([4, 1])
                
                with col1:
                    # Chat button - highlight if current
                    button_type = "primary" if chat_id == current_chat_id else "secondary"
                    
                    # Show chat title and info
                    if st.button(
                        f"💬 {title}",
                        key=f"chat_{chat_id}",
                        help=f"Messages: {message_count} | Updated: {updated.strftime('%m/%d %H:%M')}",
                        use_container_width=True,
                        type=button_type
                    ):
                        if chat_id != current_chat_id:
                            chat_manager.switch_chat(chat_id)
                
                with col2:
                    # Delete button
                    if st.button(
                        "🗑️",
                        key=f"delete_{chat_id}",
                        help="Delete this chat",
                        use_container_width=True
                    ):
                        if len(st.session_state.all_chats) > 1:  # Don't delete last chat
                            chat_manager.delete_chat(chat_id)
                        else:
                            st.error("Cannot delete the last chat!")
                
                # Show chat preview info
                st.caption(f"{message_count} messages • {updated.strftime('%m/%d %H:%M')}")
                st.markdown("---")
        
        else:
            st.info("No chats yet. Click 'New Chat' to start!")
        
        # Footer with additional actions
        st.markdown("### ⚙️ Actions")
        
        # Export all chats
        if st.button("📥 Export All Chats", use_container_width=True):
            history_json = chat_manager.export_chat_history()
            st.download_button(
                label="💾 Download JSON",
                data=history_json,
                file_name=f"chat_history_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
                mime="application/json",
                use_container_width=True
            )
        
        # Clear all chats (with confirmation)
        if st.button("🗑️ Clear All Chats", use_container_width=True):
            if st.button("⚠️ Confirm Delete All", use_container_width=True, type="secondary"):
                st.session_state.all_chats = {}
                chat_manager.create_new_chat()
                st.rerun()
        
        # Show total stats
        st.markdown("---")
        total_chats = len(st.session_state.all_chats)
        total_messages = sum(len(chat["messages"]) for chat in st.session_state.all_chats.values())
        
        col1, col2 = st.columns(2)
        with col1:
            st.metric("Chats", total_chats)
        with col2:
            st.metric("Messages", total_messages)

# =============================================================================
# MAIN CHAT INTERFACE
# =============================================================================

def render_main_chat(chat_manager):
    """Render the main chat interface"""
    
    current_chat = chat_manager.get_current_chat()
    
    if not current_chat:
        st.error("No active chat found!")
        return
    
    # Chat header with title and info
    st.title(f"🤖 {current_chat['title']}")
    
    col1, col2, col3 = st.columns([2, 1, 1])
    with col1:
        st.caption(f"Chat ID: {current_chat['id']}")
    with col2:
        st.caption(f"Created: {current_chat['created_at'].strftime('%m/%d %H:%M')}")
    with col3:
        st.caption(f"Messages: {len(current_chat['messages'])}")
    
    st.markdown("---")
    
    # Chat messages display
    chat_container = st.container()
    
    with chat_container:
        for message in current_chat["messages"]:
            role = message["role"]
            content = message["content"]
            timestamp = message["timestamp"].strftime("%H:%M")
            
            if role == "user":
                st.markdown(f"""
                <div style="background: linear-gradient(135deg, #667eea, #764ba2); 
                           color: white; padding: 15px; border-radius: 15px; 
                           margin: 10px 0; margin-left: 20%; text-align: right;">
                    <strong>You ({timestamp})</strong><br>{content}
                </div>
                """, unsafe_allow_html=True)
            else:
                st.markdown(f"""
                <div style="background: #f8f9fa; border: 1px solid #e9ecef;
                           padding: 15px; border-radius: 15px; 
                           margin: 10px 0; margin-right: 20%;">
                    <strong>🤖 Assistant ({timestamp})</strong><br>{content}
                </div>
                """, unsafe_allow_html=True)
    
    # Chat input
    user_input = st.chat_input("Ask me anything about Reddit discussions...")
    
    if user_input:
        # Add user message
        chat_manager.add_message_to_current_chat("user", user_input)
        
        # Show thinking
        with st.spinner("🤔 Thinking..."):
            import time
            time.sleep(1)  # Simulate processing
            
            # Generate mock response
            mock_response = f"""Based on Reddit discussions about "{user_input}", here's what I found:

This is a mock response from your RAG system. In the real implementation, this would:

1. 🔍 Search your vector database for relevant Reddit posts
2. 📝 Send context to Llama 3 API  
3. ✨ Generate this response based on Reddit discussions

*This response was generated for chat: {current_chat['title']}*"""
        
        # Add assistant response
        chat_manager.add_message_to_current_chat("assistant", mock_response)
        
        st.rerun()

# =============================================================================
# MAIN APPLICATION
# =============================================================================

def main():
    """Main application function"""
    
    # Page configuration
    st.set_page_config(
        page_title="RAG Chat with History",
        page_icon="🤖",
        layout="wide",
        initial_sidebar_state="expanded"
    )
    
    # Initialize chat manager
    chat_manager = ChatManager()
    
    # Custom CSS
    st.markdown("""
    <style>
    .main {
        padding-top: 1rem;
    }
    
    .stApp > header {
        background-color: transparent;
    }
    
    /* Sidebar styling */
    .css-1d391kg {
        background-color: #f0f2f6;
    }
    
    /* Chat input styling */
    .stChatInput {
        position: fixed;
        bottom: 0;
        background: white;
        border-top: 1px solid #ddd;
    }
    </style>
    """, unsafe_allow_html=True)
    
    # Render sidebar with chat history
    render_chat_sidebar(chat_manager)
    
    # Render main chat interface
    render_main_chat(chat_manager)
    
    # Debug info (remove in production)
    if st.checkbox("🐛 Show Debug Info"):
        st.markdown("### Debug Information")
        st.write("**Current Chat ID:**", st.session_state.current_chat_id)
        st.write("**Total Chats:**", len(st.session_state.all_chats))
        st.write("**All Chat IDs:**", list(st.session_state.all_chats.keys()))

if __name__ == "__main__":
    main()