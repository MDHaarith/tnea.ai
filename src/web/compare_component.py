
import streamlit as st
import pandas as pd

class CompareComponent:
    def __init__(self, data_engine):
        self.data_engine = data_engine

    def render_comparison(self, eligible_colleges=None):
        """
        Renders a multi-select to choose colleges and a detailed comparison table.
        """
        st.subheader("⚖️ Compare Colleges")
        
        all_colleges = self.data_engine.colleges
        source_list = eligible_colleges if eligible_colleges else all_colleges
        
        college_options = {f"{c['name']} ({c['code']})": c['code'] for c in source_list}
        
        selected_labels = st.multiselect(
            "Select colleges to compare (Max 3 recommended)",
            options=list(college_options.keys()),
            max_selections=3
        )
        
        if not selected_labels:
            st.info("Select at least 2 colleges to see a comparison.")
            return

        selected_codes = [college_options[label] for label in selected_labels]
        comparison_data = []

        for code in selected_codes:
            # Find college data
            college = next((c for c in all_colleges if c['code'] == code), None)
            if not college:
                continue
            
            # Get cutoffs info
            cutoffs = self.data_engine.get_college_cutoffs(str(code))
            cutoff_details = {}
            if cutoffs:
                latest_year = max(c['year'] for c in cutoffs)
                latest_cutoffs = [c for c in cutoffs if c['year'] == latest_year]
                for kb in ['CSE', 'ECE', 'MECH', 'IT']:
                    match = next((c for c in latest_cutoffs if c.get('branch_code') == kb), None)
                    val = match.get('cutoffs', {}).get('OC', 0) if match else 0
                    cutoff_details[f"Cutoff {kb}"] = val
            else:
                 for kb in ['CSE', 'ECE', 'MECH', 'IT']:
                    cutoff_details[f"Cutoff {kb}"] = 0

            # Safe conversion for placement
            place_val = 0
            raw_placement = college.get('placement')
            if raw_placement:
                 # Extract number from string like "85%" or "85.5 %"
                 import re
                 match = re.search(r"(\d+(\.\d+)?)", str(raw_placement))
                 if match:
                     place_val = float(match.group(1))

            # Total Seats
            total_seats = self.data_engine.get_total_seats_for_college(str(code))
            
            # Fees
            fees = "Refer Website"
            if college.get('fees'):
                try:
                    f = college['fees']
                    # Sum up known fee components if available
                    total_fee = 0
                    if 'admission' in f: total_fee += int(f['admission'])
                    if 'tuition' in f: total_fee += int(f['tuition'])
                    if total_fee > 0:
                        fees = f"₹{total_fee:,}/yr (Approx)"
                except:
                    pass

            comparison_data.append({
                "College Name": college.get('name'),
                "Code": code,
                "District": college.get('district'),
                "Placement %": place_val,
                "Total Seats": total_seats if total_seats > 0 else "N/A",
                "Autonomous": "✅ Yes" if college.get('is_autonomous') else "❌ No",
                "Estd. Year": college.get('estd_year', 'N/A'),
                "Hostel": "✅ Yes" if college.get('has_hostel') else "Check Website",
                "Fees": fees,
                **cutoff_details,
                "Website": college.get('website', 'N/A')
            })

        if comparison_data:
            df = pd.DataFrame(comparison_data)
            
            # Transpose for side-by-side view, but Streamlit dataframe is column-based, 
            # so we'll structure it to match column_config
            
            st.dataframe(
                df,
                column_config={
                    "College Name": st.column_config.TextColumn("College", width="large"),
                    "Placement %": st.column_config.ProgressColumn(
                        "Placement History",
                        format="%.1f%%",
                        min_value=0,
                        max_value=100,
                    ),
                    "Total Seats": st.column_config.NumberColumn("Total Seats"),
                    "Fees": st.column_config.TextColumn("Approx Fees"),
                    "Cutoff CSE": st.column_config.NumberColumn("CSE Cutoff", format="%.2f"),
                    "Cutoff ECE": st.column_config.NumberColumn("ECE Cutoff", format="%.2f"),
                    "Cutoff IT": st.column_config.NumberColumn("IT Cutoff", format="%.2f"),
                    "Website": st.column_config.LinkColumn("Link"),
                },
                use_container_width=True,
                hide_index=True
            )
            
            # Also show a transposed version for detailed reading
            with st.expander("Detailed Comparison View"):
                st.table(df.set_index("College Name").T)
            
            # --- Analytical Charts ---
            st.divider()
            st.subheader("📊 Analytical Comparison")
            
            import plotly.graph_objects as go
            
            # Normalize and prepare data for Radar Chart
            categories = ['Academics', 'Placement', 'Infrastructure', 'Location']
            
            fig = go.Figure()
            
            for item in comparison_data:
                # heuristic normalization
                
                # Academics: Map Cutoff to Percentile-like score
                # 200 -> 100, 190 -> 90, 180 -> 80 ... 100 -> 0
                avg_cutoff = (item.get('Cutoff CSE', 0) + item.get('Cutoff ECE', 0)) / 2
                if avg_cutoff == 0: avg_cutoff = 150 # default baseline
                academics_score = max(0, min(100, (avg_cutoff - 100))) 
                
                # Placement: Raw % is already 0-100
                placement_score = item.get('Placement %', 0)
                
                # Infrastructure
                infra_score = 40 # Base
                if "Yes" in item.get('Autonomous', ''): infra_score += 30
                if "Yes" in item.get('Hostel', ''): infra_score += 30
                
                # Location
                major_cities = ['CHENNAI', 'COIMBATORE', 'MADURAI', 'TRICHY', 'SALEM']
                loc_score = 85 if str(item.get('District', '')).upper() in major_cities else 60
                
                values = [academics_score, placement_score, infra_score, loc_score]
                
                fig.add_trace(go.Scatterpolar(
                    r=values,
                    theta=categories,
                    fill='toself',
                    name=item.get('College Name')
                ))
                
            fig.update_layout(
                polar=dict(
                    radialaxis=dict(
                        visible=True,
                        range=[0, 100]
                    )),
                showlegend=True,
                height=400,
                margin=dict(l=40, r=40, t=20, b=20)
            )
            
            st.plotly_chart(fig, use_container_width=True)
            
            # --- "Best For" Analysis ---
            st.subheader("🏆 AI Verdict: Best For...")
            col_candidates = st.columns(len(comparison_data))
            for idx, item in enumerate(comparison_data):
                with col_candidates[idx]:
                    st.markdown(f"**{item.get('College Name')}**")
                    tags = []
                    if item.get('Placement %', 0) > 90:
                        tags.append("🚀 Top Placements")
                    if item.get('Autonomous', '') == "✅ Yes":
                        tags.append("🏛️ Autonomous")
                    if item.get('Cutoff CSE', 0) > 190:
                        tags.append("🧠 High Cutoff")
                    if item.get('Place' in str(item.get('District', ''))):
                         pass 
                    
                    if not tags:
                        tags.append("⭐ Balanced Choice")
                        
                    for tag in tags:
                        st.caption(f"{tag}")
