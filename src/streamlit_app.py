import streamlit as st
import os
import sys
from datetime import datetime

# Add src to path if needed
sys.path.append(os.path.dirname(__file__))

from agent.counsellor_agent import CounsellorAgent
from agent.session_memory import SessionMemory

# Page Config
st.set_page_config(
    page_title="TNEA AI Counsellor",
    page_icon="🎓",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Custom CSS for Premium Design
st.markdown("""
<style>
    .main {
        background-color: #f8f9fa;
    }
    .stChatMessage {
        border-radius: 15px;
        padding: 10px;
        margin-bottom: 10px;
    }
    .stChatMessage.user {
        background-color: #e3f2fd;
        border: 1px solid #bbdefb;
    }
    .stChatMessage.assistant {
        background-color: #ffffff;
        border: 1px solid #e0e0e0;
        box-shadow: 0 2px 4px rgba(0,0,0,0.05);
    }
    .sidebar .sidebar-content {
        background-image: linear-gradient(#2e7d32, #1b5e20);
        color: white;
    }
    h1 {
        color: #1b5e20;
        font-family: 'Inter', sans-serif;
        font-weight: 700;
    }
    .profile-card {
        background-color: #ffffff;
        padding: 15px;
        border-radius: 10px;
        border-left: 5px solid #2e7d32;
        margin-bottom: 10px;
        color: #333;
    }
</style>
""", unsafe_allow_html=True)

# Initialize Session State
if "messages" not in st.session_state:
    st.session_state.messages = []

if "session_id" not in st.session_state:
    st.session_state.session_id = f"session_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

if "agent" not in st.session_state:
    # Initialize Memory with Session ID
    memory = SessionMemory(session_id=st.session_state.session_id)
    # The agent uses the provided memory
    st.session_state.agent = CounsellorAgent(memory=memory)

# Title
st.title("🎓 TNEA AI Expert Counsellor")
st.markdown("---")

# Sidebar - Student Profile
with st.sidebar:
    st.header("👤 Student Profile")
    st.info("The AI uses this data to provide personalized recommendations.")
    
    # Profile Display
    profile = st.session_state.agent.memory.user_profile
    
    with st.container():
        st.markdown(f"""
        <div class="profile-card">
            <strong>Cutoff Mark:</strong> {profile.get('mark') or '--'}<br>
            <strong>Rank:</strong> {profile.get('rank') or '--'}<br>
            <strong>Percentile:</strong> {profile.get('percentile') or '--'}<br>
            <strong>Location:</strong> {profile.get('preferred_location') or '--'}<br>
            <strong>Branch:</strong> {profile.get('preferred_branch') or '--'}
        </div>
        """, unsafe_allow_html=True)
    
    st.markdown("---")
    
    # Save/Load Info
    st.subheader("💾 Session History")
    st.write(f"Session ID: `{st.session_state.session_id}`")
    
    if st.button("Clear Chat"):
        st.session_state.messages = []
        st.session_state.agent.memory.history = []
        st.session_state.agent.memory.save_to_json()
        st.rerun()

# Display Chat History
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# User Input
if prompt := st.chat_input("Ask about TNEA counselling, colleges, or career paths..."):
    # Clear visual feedback for processing
    with st.chat_message("user"):
        st.markdown(prompt)
    
    # Add to session state history
    st.session_state.messages.append({"role": "user", "content": prompt})
    
    # Generate Assistant Response
    with st.chat_message("assistant"):
        response_placeholder = st.empty()
        full_response = ""
        
        try:
            # use generator from agent
            for chunk in st.session_state.agent.process_query_stream(prompt):
                full_response += chunk
                response_placeholder.markdown(full_response + "▌")
            
            response_placeholder.markdown(full_response)
            
            # Add to history
            st.session_state.messages.append({"role": "assistant", "content": full_response})
            
            # Sync Profile in Sidebar
            st.sidebar.empty() # Force refresh sidebar values next run if possible
            # Note: streamlit usually syncs on next rerun.
            
        except Exception as e:
            st.error(f"Error: {e}")
            full_response = "I encountered an error while processing your request. Please try again."
            response_placeholder.markdown(full_response)

    # Rerun to update sidebar and state properly
    st.rerun()
