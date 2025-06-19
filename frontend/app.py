"""
Streamlit Test Frontend for Web Assistant API

This is a simple frontend for testing the Web Assistant API endpoints.
It provides a user-friendly interface for registration, login, session management, and chat.
"""

import streamlit as st
import requests
import json
from datetime import datetime
from typing import Dict, List, Optional

# Configuration
API_BASE_URL = "http://127.0.0.1:8000/api/v1"

# Page configuration
st.set_page_config(
    page_title="Web Assistant Test UI",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Using Streamlit default styles

# Session state initialization
if 'user_token' not in st.session_state:
    st.session_state.user_token = None
if 'current_session' not in st.session_state:
    st.session_state.current_session = None
if 'sessions' not in st.session_state:
    st.session_state.sessions = []
if 'messages' not in st.session_state:
    st.session_state.messages = []
if 'user_email' not in st.session_state:
    st.session_state.user_email = None

# API Helper Functions
def register_user(email: str, password: str) -> Dict:
    """Register a new user."""
    try:
        response = requests.post(
            f"{API_BASE_URL}/auth/register",
            json={"email": email, "password": password},
            headers={"Content-Type": "application/json"}
        )
        return {"success": response.status_code == 200, "data": response.json() if response.status_code == 200 else None, "error": response.text if response.status_code != 200 else None}
    except Exception as e:
        return {"success": False, "error": str(e)}

def login_user(email: str, password: str) -> Dict:
    """Login a user."""
    try:
        response = requests.post(
            f"{API_BASE_URL}/auth/login",
            data={"username": email, "password": password, "grant_type": "password"},
            headers={"Content-Type": "application/x-www-form-urlencoded"}
        )
        return {"success": response.status_code == 200, "data": response.json() if response.status_code == 200 else None, "error": response.text if response.status_code != 200 else None}
    except Exception as e:
        return {"success": False, "error": str(e)}

def create_session(token: str) -> Dict:
    """Create a new chat session."""
    try:
        response = requests.post(
            f"{API_BASE_URL}/auth/session",
            headers={"Authorization": f"Bearer {token}"}
        )
        return {"success": response.status_code == 200, "data": response.json() if response.status_code == 200 else None, "error": response.text if response.status_code != 200 else None}
    except Exception as e:
        return {"success": False, "error": str(e)}

def get_user_sessions(token: str) -> Dict:
    """Get all user sessions."""
    try:
        response = requests.get(
            f"{API_BASE_URL}/auth/sessions",
            headers={"Authorization": f"Bearer {token}"}
        )
        return {"success": response.status_code == 200, "data": response.json() if response.status_code == 200 else None, "error": response.text if response.status_code != 200 else None}
    except Exception as e:
        return {"success": False, "error": str(e)}

def send_chat_message(session_token: str, messages: List[Dict]) -> Dict:
    """Send a chat message."""
    try:
        response = requests.post(
            f"{API_BASE_URL}/chatbot/chat",
            json={"messages": messages},
            headers={"Authorization": f"Bearer {session_token}", "Content-Type": "application/json"}
        )
        return {"success": response.status_code == 200, "data": response.json() if response.status_code == 200 else None, "error": response.text if response.status_code != 200 else None}
    except Exception as e:
        return {"success": False, "error": str(e)}

def get_session_messages(session_token: str) -> Dict:
    """Get messages for a session."""
    try:
        response = requests.get(
            f"{API_BASE_URL}/chatbot/messages",
            headers={"Authorization": f"Bearer {session_token}"}
        )
        return {"success": response.status_code == 200, "data": response.json() if response.status_code == 200 else None, "error": response.text if response.status_code != 200 else None}
    except Exception as e:
        return {"success": False, "error": str(e)}

def clear_session_messages(session_token: str) -> Dict:
    """Clear messages for a session."""
    try:
        response = requests.delete(
            f"{API_BASE_URL}/chatbot/messages",
            headers={"Authorization": f"Bearer {session_token}"}
        )
        return {"success": response.status_code == 200, "data": response.json() if response.status_code == 200 else None, "error": response.text if response.status_code != 200 else None}
    except Exception as e:
        return {"success": False, "error": str(e)}



# UI Components
def render_auth_section():
    """Render authentication section."""
    st.header("🔐 Authentication")
    
    auth_tab1, auth_tab2 = st.tabs(["Login", "Register"])
    
    with auth_tab1:
        st.subheader("Login")
        with st.form("login_form"):
            login_email = st.text_input("Email", key="login_email")
            login_password = st.text_input("Password", type="password", key="login_password")
            login_submit = st.form_submit_button("Login")
            
            if login_submit:
                if login_email and login_password:
                    with st.spinner("Logging in..."):
                        result = login_user(login_email, login_password)
                        if result["success"]:
                            st.session_state.user_token = result["data"]["access_token"]
                            st.session_state.user_email = login_email
                            st.success("✅ Login successful!")
                            st.rerun()
                        else:
                            st.error(f"❌ Login failed: {result['error']}")
                else:
                    st.error("Please fill in all fields")
    
    with auth_tab2:
        st.subheader("Register")
        with st.form("register_form"):
            reg_email = st.text_input("Email", key="reg_email")
            reg_password = st.text_input("Password", type="password", key="reg_password")
            reg_submit = st.form_submit_button("Register")
            
            if reg_submit:
                if reg_email and reg_password:
                    with st.spinner("Registering..."):
                        result = register_user(reg_email, reg_password)
                        if result["success"]:
                            st.session_state.user_token = result["data"]["token"]["access_token"]
                            st.session_state.user_email = reg_email
                            st.success("✅ Registration successful!")
                            st.rerun()
                        else:
                            st.error(f"❌ Registration failed: {result['error']}")
                else:
                    st.error("Please fill in all fields")

def render_session_management():
    """Render session management section."""
    st.header("💬 Session Management")
    
    col1, col2 = st.columns([1, 1])
    
    with col1:
        if st.button("🔄 Refresh Sessions", use_container_width=True):
            with st.spinner("Loading sessions..."):
                result = get_user_sessions(st.session_state.user_token)
                if result["success"]:
                    st.session_state.sessions = result["data"]
                    st.success("Sessions refreshed!")
                else:
                    st.error(f"Failed to load sessions: {result['error']}")
    
    with col2:
        if st.button("➕ Create New Session", use_container_width=True):
            with st.spinner("Creating session..."):
                result = create_session(st.session_state.user_token)
                if result["success"]:
                    st.session_state.current_session = result["data"]
                    st.success("New session created!")
                    # Refresh sessions list
                    sessions_result = get_user_sessions(st.session_state.user_token)
                    if sessions_result["success"]:
                        st.session_state.sessions = sessions_result["data"]
                    st.rerun()
                else:
                    st.error(f"Failed to create session: {result['error']}")
    
    # Display sessions
    if st.session_state.sessions:
        st.subheader("Your Sessions")
        for session in st.session_state.sessions:
            session_name = session.get("name", f"Session {session['session_id'][:8]}")
            if session_name == "":
                session_name = f"Session {session['session_id'][:8]}"
            
            if st.button(
                f"📝 {session_name}",
                key=f"session_{session['session_id']}",
                use_container_width=True
            ):
                st.session_state.current_session = session
                # Load messages for this session
                with st.spinner("Loading messages..."):
                    result = get_session_messages(session["token"]["access_token"])
                    if result["success"]:
                        st.session_state.messages = result["data"]["messages"]
                    else:
                        st.session_state.messages = []
                st.rerun()

def render_chat_interface():
    """Render chat interface."""
    if not st.session_state.current_session:
        st.info("Please select or create a session to start chatting.")
        return
    
    st.header(f"💬 Chat - {st.session_state.current_session.get('name', f'Session {st.session_state.current_session['session_id'][:8]}')}")
    
    # Chat controls
    col1, col2, col3 = st.columns([2, 1, 1])
    
    with col1:
        st.text(f"Session ID: {st.session_state.current_session['session_id'][:8]}...")
    
    with col2:
        if st.button("🔄 Refresh Messages"):
            with st.spinner("Loading messages..."):
                result = get_session_messages(st.session_state.current_session["token"]["access_token"])
                if result["success"]:
                    st.session_state.messages = result["data"]["messages"]
                    st.rerun()
                else:
                    st.error(f"Failed to load messages: {result['error']}")
    
    with col3:
        if st.button("🗑️ Clear Chat"):
            with st.spinner("Clearing chat..."):
                result = clear_session_messages(st.session_state.current_session["token"]["access_token"])
                if result["success"]:
                    st.session_state.messages = []
                    st.success("Chat cleared!")
                    st.rerun()
                else:
                    st.error(f"Failed to clear chat: {result['error']}")
    
    # Messages display
    st.subheader("Messages")
    messages_container = st.container()
    
    with messages_container:
        if st.session_state.messages:
            for msg in st.session_state.messages:
                role = msg.get("role", "unknown")
                content = msg.get("content", "")
                
                if role == "user":
                    with st.chat_message("user"):
                        st.write(content)
                elif role == "assistant":
                    with st.chat_message("assistant"):
                        st.write(content)
        else:
            st.info("No messages yet. Start a conversation!")
    
    # Message input
    st.subheader("Send Message")
    with st.form("chat_form", clear_on_submit=True):
        user_input = st.text_area("Your message:", height=100, key="user_message_input")
        send_button = st.form_submit_button("Send 📤", use_container_width=True)
        
        if send_button and user_input.strip():
            # Prepare messages to send (don't modify local state yet)
            messages_to_send = st.session_state.messages + [{"role": "user", "content": user_input.strip()}]
            
            with st.spinner("Getting response..."):
                result = send_chat_message(
                    st.session_state.current_session["token"]["access_token"],
                    messages_to_send
                )
                
                if result["success"]:
                    # Trust backend as source of truth - replace entire message list
                    st.session_state.messages = result["data"]["messages"]
                    st.success("Message sent!")
                    st.rerun()
                else:
                    st.error(f"Failed to send message: {result['error']}")

def render_sidebar():
    """Render sidebar with user info and controls."""
    with st.sidebar:
        st.title("🤖 Web Assistant")
        st.markdown("---")
        
        if st.session_state.user_token:
            st.success(f"Logged in as: {st.session_state.user_email}")
            
            if st.button("🚪 Logout", use_container_width=True):
                st.session_state.user_token = None
                st.session_state.current_session = None
                st.session_state.sessions = []
                st.session_state.messages = []
                st.session_state.user_email = None
                st.rerun()
            
            st.markdown("---")
            
            # Session info
            if st.session_state.current_session:
                st.subheader("Current Session")
                session_name = st.session_state.current_session.get("name", f"Session {st.session_state.current_session['session_id'][:8]}")
                st.info(f"📝 {session_name}")
                st.text(f"ID: {st.session_state.current_session['session_id'][:16]}...")
                
                # Message count
                msg_count = len(st.session_state.messages)
                st.metric("Messages", msg_count)
        else:
            st.info("Please login to continue")
        
        st.markdown("---")
        st.markdown("### 📚 API Endpoints")
        st.markdown("""
        - **Auth**: `/auth/register`, `/auth/login`
        - **Sessions**: `/auth/session`, `/auth/sessions`
        - **Chat**: `/chatbot/chat`, `/chatbot/messages`
        - **Docs**: [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)
        """)

# Main App
def main():
    """Main application function."""
    render_sidebar()
    
    if not st.session_state.user_token:
        render_auth_section()
    else:
        # Main content tabs
        tab1, tab2 = st.tabs(["💬 Chat", "⚙️ Sessions"])
        
        with tab1:
            render_chat_interface()
        
        with tab2:
            render_session_management()

if __name__ == "__main__":
    main() 