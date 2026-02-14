import streamlit as st
import os
import sys
from datetime import datetime
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

# Add src to path if needed
sys.path.append(os.path.dirname(__file__))

from agent.counsellor_agent import CounsellorAgent
from agent.session_memory import SessionMemory

# Page Config
st.set_page_config(
    page_title="🎓 TNEA AI Expert Counsellor - Advanced Edition",
    page_icon="🎓",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Custom CSS for Premium Design
st.markdown("""
<style>
    .main {
        background: linear-gradient(135deg, #F6E7BC 0%, #FFF8E1 100%);
    }
    .stChatMessage {
        border-radius: 15px;
        padding: 15px;
        margin-bottom: 15px;
        box-shadow: 0 4px 6px rgba(11, 45, 114, 0.1);
    }
    .stChatMessage.user {
        background: linear-gradient(135deg, #0992C2 0%, #0AC4E0 100%);
        border: 1px solid #0B2D72;
        color: white;
    }
    .stChatMessage.assistant {
        background: #ffffff;
        border: 1px solid #0AC4E0;
        color: #0B2D72;
    }
    .metric-card {
        background: #ffffff;
        color: #0B2D72;
        padding: 15px;
        border-radius: 10px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        border-left: 5px solid #0B2D72;
    }
    .profile-card {
        background: #ffffff;
        color: #0B2D72;
        padding: 15px;
        border-radius: 10px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        border-left: 5px solid #0992C2;
    }
    .college-card {
        background: #f8f9fa;
        color: #333333;
        padding: 15px;
        border-radius: 10px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        border: 1px solid #e0e0e0;
        margin-bottom: 10px;
    }
    .safe-college {
        border-left: 5px solid #4caf50 !important;
    }
    .moderate-college {
        border-left: 5px solid #ff9800 !important;
    }
    .ambitious-college {
        border-left: 5px solid #f44336 !important;
    }
    .header {
        text-align: center;
        background: linear-gradient(135deg, #0B2D72 0%, #0992C2 100%);
        color: #F6E7BC;
        padding: 20px;
        border-radius: 10px;
        margin-bottom: 20px;
    }
    .footer {
        text-align: center;
        padding: 20px;
        color: #0B2D72;
        font-size: 0.9em;
    }
    /* Responsive Design */
    @media (max-width: 768px) {
        .stChatMessage {
            padding: 10px;
            margin-bottom: 10px;
        }
        .header {
            padding: 15px;
        }
        .header h1 {
            font-size: 1.5rem;
        }
        .header h3 {
            font-size: 1rem;
        }
        .metric-card, .profile-card, .college-card {
            margin-bottom: 10px;
        }
    }
    /* Chat Input Styling */
    .stChatInput {
        border: 2px solid #0AC4E0 !important;
        border-radius: 10px !important;
        padding: 0px !important;
        transition: all 0.3s ease;
        background-color: transparent !important;
    }
    .stChatInput > div {
        padding: 5px !important;
    }
    .stChatInput:focus-within {
        box-shadow: 0 0 15px rgba(10, 196, 224, 0.3) !important;
        border-color: #0992C2 !important;
        transform: translateY(-2px);
    }
</style>

<script>
    function scrollToBottom() {
        const messages = parent.document.querySelector('[data-testid="stChatMessageContainer"]') || 
                        parent.document.querySelector('.stChatMessageContainer');
        if (messages) {
            messages.scrollTop = messages.scrollHeight;
        }
    }
    
    function focusChatInput() {
        const input = parent.document.querySelector('textarea[data-testid="stChatInputTextArea"]');
        if (input) {
            input.focus();
        }
    }

    // Observer to watch for new messages and scroll
    const observer = new MutationObserver((mutations) => {
        scrollToBottom();
        // Also check if input became available/needs focus
        if (!parent.document.activeElement || parent.document.activeElement.tagName !== 'TEXTAREA') {
            focusChatInput();
        }
    });
    
    const config = { childList: true, subtree: true };
    const target = parent.document.querySelector('[data-testid="stChatMessageContainer"]') || 
                  parent.document.querySelector('.stChatMessageContainer');
                  
    // Also observe the main container for view changes
    const mainContainer = parent.document.querySelector('.main');
    
    if (target) {
        observer.observe(target, config);
        scrollToBottom(); 
    }
    if (mainContainer) {
        observer.observe(mainContainer, config);
    }
    
    // Initial focus attempt
    setTimeout(focusChatInput, 500);
</script>
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

if "current_view" not in st.session_state:
    st.session_state.current_view = "chat"

if "user_data" not in st.session_state:
    st.session_state.user_data = {
        "mark": None,
        "rank": None,
        "percentile": None,
        "location": None,
        "branch": None,
        "community": "OC"
    }

# Header
st.markdown('<div class="header"><h1>🎓 TNEA AI Expert Counsellor</h1><h3>Advanced Engineering Admission Advisor</h3></div>', unsafe_allow_html=True)

# Navigation
with st.container():
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        if st.button("💬 Chat", use_container_width=True, type="primary" if st.session_state.current_view == "chat" else "secondary"):
            st.session_state.current_view = "chat"
            st.rerun()
    with col2:
        if st.button("📊 Analytics", use_container_width=True, type="primary" if st.session_state.current_view == "analytics" else "secondary"):
            st.session_state.current_view = "analytics"
            st.rerun()
    with col3:
        if st.button("📋 Recommend", use_container_width=True, type="primary" if st.session_state.current_view == "recommendations" else "secondary"):
            st.session_state.current_view = "recommendations"
            st.rerun()
    with col4:
        if st.button("⚙️ Profile", use_container_width=True, type="primary" if st.session_state.current_view == "profile" else "secondary"):
            st.session_state.current_view = "profile"
            st.rerun()

# Sidebar - Student Profile
with st.sidebar:
    st.header("👤 Student Profile")
    st.info("Configure your profile for personalized recommendations")
    
    # Profile Display
    profile = st.session_state.agent.memory.user_profile
    
    with st.container():
        st.markdown(f"""
        <div class="profile-card">
            <strong>🏆 Estimated Rank:</strong> {profile.get('rank') or 'Pending'}<br>
            <strong>🎯 Cutoff Mark:</strong> {profile.get('mark') or 'Not set'}<br>
            <strong>📈 Percentile:</strong> {profile.get('percentile') or 'Pending'}<br>
            <strong>📍 Location:</strong> {profile.get('preferred_location') or 'Not set'}<br>
            <strong>🎓 Branch:</strong> {profile.get('preferred_branch') or 'Not set'}<br>
            <strong>👥 Community:</strong> {profile.get('community') or 'OC'}
        </div>
        """, unsafe_allow_html=True)
    
    st.markdown("---")
    
    
    st.markdown("---")

    
    # Save/Load Info
    st.subheader("💾 Session")
    st.write(f"ID: `{st.session_state.session_id}`")
    
    if st.button("🔄 Clear Chat", use_container_width=True):
        st.session_state.messages = []
        st.session_state.agent.memory.history = []
        st.session_state.agent.memory.save_to_json()
        st.rerun()

    with st.expander("📊 Export Data", expanded=False):
        # Prepare data for export
        export_data = {
            "profile": st.session_state.agent.memory.user_profile,
            "session_id": st.session_state.session_id,
            "timestamp": datetime.now().isoformat()
        }
        
        # JSON Export
        import json
        json_str = json.dumps(export_data, indent=2)
        st.download_button(
            label="Download as JSON",
            data=json_str,
            file_name=f"tnea_data_{st.session_state.session_id}.json",
            mime="application/json",
            use_container_width=True
        )
        
        # Excel Export
        try:
            import io
            # Flatten profile for Excel
            flat_profile = pd.DataFrame([st.session_state.agent.memory.user_profile])
            
            # Create Excel file in memory
            buffer = io.BytesIO()
            with pd.ExcelWriter(buffer, engine='xlsxwriter') as writer:
                flat_profile.to_excel(writer, sheet_name='Profile', index=False)
                
                # Chat History
                if st.session_state.messages:
                    chat_df = pd.DataFrame(st.session_state.messages)
                    chat_df.to_excel(writer, sheet_name='Chat History', index=False)
            
            st.download_button(
                label="Download as Excel",
                data=buffer.getvalue(),
                file_name=f"tnea_data_{st.session_state.session_id}.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                use_container_width=True
            )
        except Exception as e:
            st.error(f"Excel export not available: {e}")

# Main Content Area
if st.session_state.current_view == "chat":
    # Display Chat History
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    # User Input
    if prompt := st.chat_input("Ask about TNEA counselling, colleges, ranks, or career paths..."):
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
                
                # Auto-scroll and focus after response
                st.components.v1.html(
                    """
                    <script>
                        var chatContainer = window.parent.document.querySelector('[data-testid="stChatMessageContainer"]');
                        if (chatContainer) {
                            chatContainer.scrollTop = chatContainer.scrollHeight;
                        }
                        var input = window.parent.document.querySelector('textarea[data-testid="stChatInputTextArea"]');
                        if (input) {
                            input.focus();
                        }
                    </script>
                    """,
                    height=0,
                    width=0,
                )
                
                # Add to history
                st.session_state.messages.append({"role": "assistant", "content": full_response})
                
            except Exception as e:
                st.error(f"Error: {e}")
                full_response = "I encountered an error while processing your request. Please try again."
                response_placeholder.markdown(full_response)

elif st.session_state.current_view == "analytics":
    st.header("📊 Analytics Dashboard")
    
    # Load analytics data
    profile = st.session_state.agent.memory.user_profile
    
    if profile.get('mark') and profile.get('percentile') and profile.get('rank'):
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.markdown(f"""
            <div class="metric-card">
                <h3>🏆 Estimated Rank</h3>
                <h1 style="color: #ff9800;">~{profile.get('rank')}</h1>
                <p>Out of {st.session_state.agent.predictor.total_students:,} Students</p>
            </div>
            """, unsafe_allow_html=True)
        
        with col2:
            st.markdown(f"""
            <div class="metric-card">
                <h3>🎯 Your Cutoff</h3>
                <h1 style="color: #1976d2;">{profile.get('mark')}</h1>
                <p>Competitive Score</p>
            </div>
            """, unsafe_allow_html=True)
        
        with col3:
            st.markdown(f"""
            <div class="metric-card">
                <h3>📈 Percentile</h3>
                <h1 style="color: #4caf50;">{profile.get('percentile'):.2f}%</h1>
                <p>Top {100 - profile.get('percentile'):.2f}% of Students</p>
            </div>
            """, unsafe_allow_html=True)
        
        # Visualization
        st.subheader("Performance Visualization")
        
        # Create a simple chart
        fig = go.Figure(go.Indicator(
            mode="gauge+number+delta",
            value=profile.get('percentile'),
            domain={'x': [0, 1], 'y': [0, 1]},
            title={'text': "Percentile Performance"},
            delta={'reference': 50},
            gauge={
                'axis': {'range': [None, 100], 'tickwidth': 1, 'tickcolor': "darkblue"},
                'bar': {'color': "darkblue"},
                'bgcolor': "white",
                'borderwidth': 2,
                'bordercolor': "gray",
                'steps': [
                    {'range': [0, 50], 'color': 'lightcoral'},
                    {'range': [50, 80], 'color': 'lightsalmon'},
                    {'range': [80, 90], 'color': 'lightyellow'},
                    {'range': [90, 100], 'color': 'lightgreen'}
                ],
                'threshold': {
                    'line': {'color': "red", 'width': 4},
                    'thickness': 0.75,
                    'value': profile.get('percentile')
                }
            }
        ))
        
        fig.update_layout(height=300)
        st.plotly_chart(fig, use_container_width=True)
        
    else:
        st.info("Enter your cutoff mark in the Profile section to see analytics.")
        if st.button("Go to Profile"):
            st.session_state.current_view = "profile"
            st.rerun()

elif st.session_state.current_view == "recommendations":
    st.header("📋 Personalized Recommendations")
    
    profile = st.session_state.agent.memory.user_profile
    
    if not profile.get('mark'):
        st.info("Set your cutoff mark in the Profile section to get personalized recommendations.")
        if st.button("Go to Profile"):
            st.session_state.current_view = "profile"
            st.rerun()
    else:
        st.subheader(f"Recommendations for Mark: {profile.get('mark')}")
        
        # Generate recommendations using the agent
        with st.spinner("Analyzing your profile and generating recommendations..."):
            # Create a temporary query to get recommendations
            query = f"Based on cutoff mark {profile.get('mark')}, suggest colleges for me"
            if profile.get('preferred_location'):
                query += f" in {profile.get('preferred_location')}"
            if profile.get('preferred_branch'):
                query += f" for {profile.get('preferred_branch')} branch"
            
            try:
                # Get recommendations by calling the agent's internal methods
                user_mark = float(profile.get('mark'))
                community = profile.get('community', 'OC')
                
                # Use the agent's internal logic to get college suggestions
                nearby_colleges = st.session_state.agent.data_engine.colleges
                if profile.get('preferred_location'):
                    nearby_colleges = st.session_state.agent.geo_locator.find_nearby_colleges(profile.get('preferred_location'))
                
                enriched = st.session_state.agent._enrich_with_cutoffs(nearby_colleges, community)
                
                if profile.get('preferred_branch'):
                    enriched = st.session_state.agent._filter_by_branch(enriched, profile.get('preferred_branch'))
                
                if enriched:
                    categorized = st.session_state.agent.choice_strategy.categorize_options(user_mark, enriched)
                    
                    # Display categorized recommendations
                    # Display categorized recommendations
                    if categorized.get('Safe'):
                        st.subheader("✅ Safe Choices (High Probability)")
                        for college in categorized['Safe'][:7]:  # Top 7
                            # Calculate estimated rank and match score
                            cutoff_val = float(college.get('cutoff_mark', 0))
                            est_percentile = st.session_state.agent.predictor.predict_percentile(cutoff_val)
                            est_rank = st.session_state.agent.predictor.predict_rank(est_percentile)
                            
                            # Match Score Logic
                            diff = abs(user_mark - cutoff_val)
                            match_score = max(0, int(100 - (diff * 2)))
                            if match_score > 98: match_score = 99 # Cap slightly below 100 to be realistic
                            
                            with st.container():
                                st.markdown(f"""
                                <div class="college-card safe-college">
                                    <div style="display: flex; justify-content: space-between; align-items: center;">
                                        <strong>{college.get('name', 'N/A')}</strong>
                                        <span style="background-color: #e8f5e9; color: #2e7d32; padding: 2px 8px; border-radius: 12px; font-size: 0.8em; border: 1px solid #c8e6c9;">Match: {match_score}%</span>
                                    </div>
                                    <span style="color: #555;">Est. Rank: <strong>~{est_rank}</strong></span><br>
                                    Branch: {college.get('branch_name', 'N/A')}<br>
                                    Cutoff: {college.get('cutoff_mark', 'N/A')}<br>
                                    District: {college.get('district', 'N/A')}<br>
                                    Placement: {college.get('placement', 'N/A')}
                                </div>
                                """, unsafe_allow_html=True)
                    
                    if categorized.get('Moderate'):
                        st.subheader("⚖️ Moderate Choices (Good Probability)")
                        for college in categorized['Moderate'][:7]:  # Top 7
                            # Calculate estimated rank and match score
                            cutoff_val = float(college.get('cutoff_mark', 0))
                            est_percentile = st.session_state.agent.predictor.predict_percentile(cutoff_val)
                            est_rank = st.session_state.agent.predictor.predict_rank(est_percentile)

                            # Match Score Logic
                            diff = abs(user_mark - cutoff_val)
                            match_score = max(0, int(100 - (diff * 2)))
                            
                            with st.container():
                                st.markdown(f"""
                                <div class="college-card moderate-college">
                                    <div style="display: flex; justify-content: space-between; align-items: center;">
                                        <strong>{college.get('name', 'N/A')}</strong>
                                        <span style="background-color: #fff3e0; color: #ef6c00; padding: 2px 8px; border-radius: 12px; font-size: 0.8em; border: 1px solid #ffe0b2;">Match: {match_score}%</span>
                                    </div>
                                    <span style="color: #555;">Est. Rank: <strong>~{est_rank}</strong></span><br>
                                    Branch: {college.get('branch_name', 'N/A')}<br>
                                    Cutoff: {college.get('cutoff_mark', 'N/A')}<br>
                                    District: {college.get('district', 'N/A')}<br>
                                    Placement: {college.get('placement', 'N/A')}
                                </div>
                                """, unsafe_allow_html=True)
                    
                    if categorized.get('Ambitious'):
                        st.subheader("🚀 Ambitious Choices (Reach Goals)")
                        for college in categorized['Ambitious'][:6]:  # Top 6
                            # Calculate estimated rank and match score
                            cutoff_val = float(college.get('cutoff_mark', 0))
                            est_percentile = st.session_state.agent.predictor.predict_percentile(cutoff_val)
                            est_rank = st.session_state.agent.predictor.predict_rank(est_percentile)

                            # Match Score Logic
                            diff = abs(user_mark - cutoff_val)
                            match_score = max(0, int(100 - (diff * 2)))

                            with st.container():
                                st.markdown(f"""
                                <div class="college-card ambitious-college">
                                    <div style="display: flex; justify-content: space-between; align-items: center;">
                                        <strong>{college.get('name', 'N/A')}</strong>
                                        <span style="background-color: #ffebee; color: #c62828; padding: 2px 8px; border-radius: 12px; font-size: 0.8em; border: 1px solid #ffcdd2;">Match: {match_score}%</span>
                                    </div>
                                    <span style="color: #555;">Est. Rank: <strong>~{est_rank}</strong></span><br>
                                    Branch: {college.get('branch_name', 'N/A')}<br>
                                    Cutoff: {college.get('cutoff_mark', 'N/A')}<br>
                                    District: {college.get('district', 'N/A')}<br>
                                    Placement: {college.get('placement', 'N/A')}
                                </div>
                                """, unsafe_allow_html=True)
                else:
                    st.warning("No colleges found matching your criteria. Try adjusting your preferences.")
            except Exception as e:
                st.error(f"Error generating recommendations: {e}")

elif st.session_state.current_view == "profile":
    st.header("👤 Profile Management")
    
    st.subheader("Personal Information")
    profile = st.session_state.agent.memory.user_profile
    
    with st.form("advanced_profile_form"):
        col1, col2 = st.columns(2)
        
        with col1:
            mark = st.number_input("Cutoff Mark", min_value=0.0, max_value=200.0, 
                                  value=float(profile.get('mark') or 0.0), step=0.1)
            location = st.text_input("Preferred Location", 
                                   value=profile.get('preferred_location') or "")
        
        with col2:
            branch = st.text_input("Preferred Branch", 
                                 value=profile.get('preferred_branch') or "")
            community = st.selectbox("Community", 
                                   ["OC", "BC", "BCM", "MBC", "SC", "SCA", "ST"], 
                                   index=["OC", "BC", "BCM", "MBC", "SC", "SCA", "ST"].index(profile.get('community', 'OC')))
        
        submitted = st.form_submit_button("Save Profile")
        
        if submitted:
            st.session_state.agent.memory.update_profile("mark", mark)
            st.session_state.agent.memory.update_profile("preferred_location", location)
            st.session_state.agent.memory.update_profile("preferred_branch", branch)
            st.session_state.agent.memory.update_profile("community", community)
            
            st.success("Profile updated successfully!")
    
    # Display current profile summary
    st.subheader("Current Profile Summary")
    col1, col2 = st.columns(2)
    
    with col1:
        st.metric("Estimated Rank", profile.get('rank') or "Pending")
        st.metric("Cutoff Mark", profile.get('mark') or "Not set")
    
    with col2:
        st.metric("Percentile", f"{profile.get('percentile') or 0:.2f}%" if profile.get('percentile') else "Pending")
        st.metric("Community", profile.get('community') or "OC")

# Footer
st.markdown("---")
st.markdown('<div class="footer">TNEA AI Expert Counsellor - Advanced Edition | © 2026 | Designed for Tamil Nadu Engineering Aspirants</div>', unsafe_allow_html=True)
