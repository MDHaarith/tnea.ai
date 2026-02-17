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
from web.map_component import MapComponent
from web.compare_component import CompareComponent

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
        border-radius: 30px;
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
        border-radius: 30px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        border-left: 5px solid #0B2D72;
    }
    .profile-card {
        background: #ffffff;
        color: #0B2D72;
        padding: 15px;
        border-radius: 30px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        border-left: 5px solid #0992C2;
    }

    .header {
        text-align: center;
        background: linear-gradient(135deg, #0B2D72 0%, #0992C2 100%);
        color: #F6E7BC;
        padding: 20px;
        border-radius: 30px;
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
    /* Chat Input Styling - REVERTED */
    .stChatInput {
        border: 2px solid #0AC4E0 !important;
        border-radius: 30px !important;
        padding: 0px !important;
        transition: all 0.3s ease;
        background-color: transparent !important;
    }
    
    /* Circular Send Button - KEPT */
    .stChatInput button {
        border-radius: 50% !important;
        width: 40px !important;
        height: 40px !important;
        padding: 5px !important;
        background: linear-gradient(135deg, #0992C2 0%, #0AC4E0 100%) !important;
        color: white !important;
        border: none !important;
        box-shadow: 0 2px 5px rgba(0,0,0,0.2) !important;
        transition: all 0.2s ease;
    }
    .stChatInput button:hover {
        transform: scale(1.1);
        box-shadow: 0 4px 8px rgba(0,0,0,0.3) !important;
    }
    
    .stChatInput > div {
        border-radius: 30px !important;
        padding: 5px !important;
    }
    
    .stChatInput:focus-within {
        border-radius: 30px !important;
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
    st.session_state.map_component = MapComponent(st.session_state.agent.data_engine)
    st.session_state.compare_component = CompareComponent(st.session_state.agent.data_engine)

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
    col1, col2, col3, col4, col5, col6 = st.columns(6)
    with col1:
        if st.button("💬 Chat", use_container_width=True, type="primary" if st.session_state.current_view == "chat" else "secondary"):
            st.session_state.current_view = "chat"
            st.rerun()
    with col2:
        if st.button("🔍 Search", use_container_width=True, type="primary" if st.session_state.current_view == "search" else "secondary"):
            st.session_state.current_view = "search"
            st.rerun()
    with col3:
        if st.button("📋 Recommend", use_container_width=True, type="primary" if st.session_state.current_view == "recommendations" else "secondary"):
            st.session_state.current_view = "recommendations"
            st.rerun()
    with col4:
        if st.button("⚖️ Compare", use_container_width=True, type="primary" if st.session_state.current_view == "compare" else "secondary"):
            st.session_state.current_view = "compare"
            st.rerun()
    with col5:
        if st.button("📊 Analytics", use_container_width=True, type="primary" if st.session_state.current_view == "analytics" else "secondary"):
            st.session_state.current_view = "analytics"
            st.rerun()
    with col6:
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
            
            async def run_agent_stream():
                full_response = ""
                try:
                    # use generator from agent
                    async for chunk in st.session_state.agent.process_query_stream(prompt):
                        full_response += chunk
                        response_placeholder.markdown(full_response + "▌")
                    return full_response
                except Exception as e:
                    return f"Error: {e}"

            import asyncio
            try:
                full_response = asyncio.run(run_agent_stream())
                
                # If it started with Error:, handle gracefully
                if full_response and full_response.startswith("Error:"):
                     st.error(full_response)
                else:
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
                st.error(f"Error executing async agent: {e}")
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
                <p>Out of {st.session_state.agent.predictor.predict_total_students():,} Students</p>
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
                    categorized = st.session_state.agent.choice_strategy.categorize_options(
                        user_mark, 
                        enriched, 
                        user_location=profile.get('preferred_location')
                    )
                    
                    # Display categorized recommendations
                    # Display categorized recommendations
                    # Consolidate recommendations for Table View
                    all_recommendations = []
                    
                    # Helper to process a category
                    def process_category(category_name, colleges, chance_label):
                        for college in colleges:
                            cutoff_val = float(college.get('cutoff_mark', 0))
                            p_res = st.session_state.agent.predictor.predict_percentile(cutoff_val)
                            est_percentile = p_res['prediction'] if isinstance(p_res, dict) else p_res
                            est_rank = st.session_state.agent.predictor.predict_rank(est_percentile)
                            
                            diff = abs(user_mark - cutoff_val)
                            match_score = max(0, int(100 - (diff * 2)))
                            if match_score > 98: match_score = 99
                            
                            all_recommendations.append({
                                "College Name": college.get('name', 'N/A'),
                                "Branch": college.get('branch_name', 'N/A'),
                                "Chance": chance_label,
                                "Match %": match_score,
                                "Score": college.get('quality_score', 0),
                                "Cutoff": cutoff_val,
                                "Est. Rank": est_rank,
                                "District": college.get('district', 'N/A'),
                                "Placement %": float(college.get('placement', 0)) if college.get('placement') and str(college.get('placement')).replace('.', '', 1).isdigit() else 0,
                                "Code": college.get('code', 'N/A')
                            })

                    if categorized.get('Safe'):
                        process_category('Safe', categorized['Safe'], "High (Safe)")
                    if categorized.get('Moderate'):
                        process_category('Moderate', categorized['Moderate'], "Medium (Moderate)")
                    if categorized.get('Ambitious'):
                        process_category('Ambitious', categorized['Ambitious'], "Low (Ambitious)")

                    if all_recommendations:
                        # Create DataFrame
                        df = pd.DataFrame(all_recommendations)
                        
                        # Display Statistics
                        st.markdown(f"### Found {len(df)} Colleges matching your criteria")
                        
                        # Configure Columns
                        with st.expander("📊 View Detailed College Recommendations Table", expanded=True):
                            st.dataframe(
                                df,
                                column_config={
                                    "College Name": st.column_config.TextColumn("College", width="large"),
                                    "Branch": st.column_config.TextColumn("Branch", width="medium"),
                                    "Chance": st.column_config.Column(
                                        "Approval Chance",
                                        help="Estimated probability of admission",
                                        width="small",
                                    ),
                                    "Score": st.column_config.ProgressColumn(
                                        "Quality Score",
                                        help="Composite score based on Placement, Autonomous status, Cutoff, etc.",
                                        format="%.1f",
                                        min_value=0,
                                        max_value=100,
                                    ),
                                    "Match %": st.column_config.ProgressColumn(
                                        "Match Score",
                                        help="Relevance matching your profile",
                                        format="%d%%",
                                        min_value=0,
                                        max_value=100,
                                    ),
                                    "Cutoff": st.column_config.NumberColumn(
                                        "Cutoff",
                                        format="%.2f",
                                    ),
                                    "Placement %": st.column_config.ProgressColumn(
                                        "Placement History",
                                        format="%d%%",
                                        min_value=0,
                                        max_value=100,
                                    ),
                                },
                                use_container_width=True,
                                hide_index=True,
                            )
                        
                        # Export Option (Explicit button if dataframe export isn't enough)
                        csv = df.to_csv(index=False).encode('utf-8')
                        st.download_button(
                            label="📥 Download Recommendations as CSV",
                            data=csv,
                            file_name=f'tnea_recommendations_{profile.get("mark")}.csv',
                            mime='text/csv',
                        )

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


elif st.session_state.current_view == "search":
    st.header("🔍 Search Colleges")
    
    # Simple search interface
    search_query = st.text_input("Enter College Name or District to Search", placeholder="e.g. CEG, Coimbatore, PSG")
    
    col1, col2 = st.columns([3, 1])
    with col1:
        st.info("Switch to 'Map View' tab to see locations.")
    with col2:
        pass

    tab1, tab2 = st.tabs(["List View", "Map View"])
    
    # Filter Logic
    filtered_colleges = []
    if search_query:
        search_lower = search_query.lower()
        filtered_colleges = [
            c for c in st.session_state.agent.data_engine.colleges
            if search_lower in c.get('name', '').lower() or search_lower in c.get('district', '').lower()
        ]
    else:
        # Show all colleges by default if no query
        filtered_colleges = st.session_state.agent.data_engine.colleges
    
    
    # Reset pagination if search changes
    if 'last_search' not in st.session_state:
        st.session_state.last_search = search_query
    
    if search_query != st.session_state.last_search:
        st.session_state.list_view_page = 1
        st.session_state.last_search = search_query

    # Pagination State
    if 'list_view_page' not in st.session_state:
        st.session_state.list_view_page = 1
        
    ITEMS_PER_PAGE = 20
    
    with tab1:
        total_items = len(filtered_colleges)
        total_pages = (total_items - 1) // ITEMS_PER_PAGE + 1
        
        # Ensure page is valid
        if st.session_state.list_view_page > total_pages:
            st.session_state.list_view_page = max(1, total_pages)
            
        start_idx = (st.session_state.list_view_page - 1) * ITEMS_PER_PAGE
        end_idx = min(start_idx + ITEMS_PER_PAGE, total_items)
        
        paginated_colleges = filtered_colleges[start_idx:end_idx]
        
        # Pagination Controls (Top)
        col_prev, col_info, col_next = st.columns([1, 2, 1])
        with col_prev:
            if st.session_state.list_view_page > 1:
                if st.button("⬅️ Previous", key="prev_btn_top"):
                    st.session_state.list_view_page -= 1
                    st.rerun()
        with col_info:
            st.markdown(f"<div style='text-align: center'>Showing {start_idx + 1}-{end_idx} of {total_items} colleges</div>", unsafe_allow_html=True)
        with col_next:
            if st.session_state.list_view_page < total_pages:
                if st.button("Next ➡️", key="next_btn_top"):
                    st.session_state.list_view_page += 1
                    st.rerun()

        for c in paginated_colleges:
            with st.expander(f"{c.get('name')} ({c.get('district')})"):
                st.write(f"**Code:** {c.get('code')}")
                st.write(f"**Placement:** {c.get('placement', 'N/A')}")
                
                # Show key branch cutoffs if available
                # This assumes we can fetch cutoffs easily. Since data structure might be simple,
                # we'll try to fetch if method exists or show generic info
                # Show cutoffs for all years
                try:
                    cutoffs = st.session_state.agent.data_engine.get_college_cutoffs(str(c.get('code')))
                    if cutoffs:
                        # Process data for all years
                        cutoff_data = {}
                        years = sorted(list(set(x['year'] for x in cutoffs)), reverse=True)
                        
                        # Get all branches with full names
                        # Map branch_code to branch_name from the data itself
                        branch_map = {}
                        for x in cutoffs:
                            if x.get('branch_code') and x.get('branch_name'):
                                branch_map[x['branch_code']] = x['branch_name']
                        
                        all_branch_codes = sorted(list(set(x['branch_code'] for x in cutoffs)))
                        
                        for b_code in all_branch_codes:
                            b_name = branch_map.get(b_code, b_code)
                            cutoff_data[b_name] = {}
                            
                            for year in years:
                                match = next((x for x in cutoffs if x['year'] == year and x['branch_code'] == b_code), None)
                                if match:
                                    # Get Cutoff
                                    val = match.get('cutoffs', {}).get('OC', '-')
                                    
                                    # specific logic for 2025 to show Rank
                                    if year == 2025:
                                        rank = match.get('ranks', {}).get('OC') if match.get('ranks') else None
                                        if val != '-' and rank:
                                            cutoff_data[b_name][f"{year} Cutoff (Rank)"] = f"{val} (#{rank})"
                                        elif val != '-':
                                            cutoff_data[b_name][f"{year} Cutoff (Rank)"] = f"{val}"
                                        else:
                                            cutoff_data[b_name][f"{year} Cutoff (Rank)"] = "-"
                                    else:
                                        cutoff_data[b_name][str(year)] = val
                                else:
                                    if year == 2025:
                                        cutoff_data[b_name][f"{year} Cutoff (Rank)"] = "-"
                                    else:
                                        cutoff_data[b_name][str(year)] = "-"
                        
                        # Create DataFrame
                        df_cutoffs = pd.DataFrame.from_dict(cutoff_data, orient='index')
                        
                        # Reorder columns to ensure 2025 is first, then descending
                        cols = []
                        if 2025 in years:
                            cols.append("2025 Cutoff (Rank)")
                        for y in years:
                            if y != 2025:
                                cols.append(str(y))
                                
                        # Filter cols that actually exist in df
                        valid_cols = [c for c in cols if c in df_cutoffs.columns]
                        df_cutoffs = df_cutoffs[valid_cols]
                        
                        st.write("**Cutoff Trends (OC) - Mark & (Rank):**")
                        st.dataframe(df_cutoffs, use_container_width=True)
                    else:
                        st.info("No cutoff data available.")
                except Exception as e:
                    st.error(f"Error loading cutoffs: {e}")

                if c.get('website'):
                    st.markdown(f"[Visit Website]({c.get('website')})")
    
    with tab2:
        col_map_1, col_map_2 = st.columns([3, 1])
        with col_map_1:
             st.write("### 🗺️ College Map")
        with col_map_2:
             my_loc = st.text_input("📍 My Location", placeholder="e.g. Salem", key="user_map_loc")
        
        user_coords = None
        if my_loc:
            # Use the agent's geo locator to resolve
            user_coords = st.session_state.agent.geo_locator._resolve_location(my_loc)
            if not user_coords:
                st.toast("Location not found", icon="⚠️")

        st.session_state.map_component.render_map(filtered_colleges, user_location=user_coords)

elif st.session_state.current_view == "compare":
    st.session_state.compare_component.render_comparison()

# Footer
st.markdown("---")
st.markdown('<div class="footer">TNEA AI Expert Counsellor - Advanced Edition | © 2026 | Designed for Tamil Nadu Engineering Aspirants</div>', unsafe_allow_html=True)
