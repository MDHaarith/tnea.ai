
import streamlit as st
import pandas as pd

class CompareComponent:
    def __init__(self, data_engine):
        self.data_engine = data_engine

    def render_comparison(self, eligible_colleges=None, user_profile=None):
        """
        Renders a multi-select to choose colleges and a detailed comparison table.
        user_profile: Dict with 'mark', 'community', etc.
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

        user_mark = float(user_profile.get('mark', 0)) if user_profile else 0
        user_comm = user_profile.get('community', 'OC') if user_profile else 'OC'

        for code in selected_codes:
            # Find college data
            college = next((c for c in all_colleges if c['code'] == code), None)
            if not college:
                continue
            
            # Get cutoffs info
            cutoffs = self.data_engine.get_college_cutoffs(str(code))
            cutoff_details = {}
            avg_cutoff = 0
            
            if cutoffs:
                latest_year = max(c['year'] for c in cutoffs)
                latest_cutoffs = [c for c in cutoffs if c['year'] == latest_year]
                
                # Calculate average cutoff for Quality Score
                total_c = 0
                count_c = 0
                
                for kb in ['CSE', 'ECE', 'MECH', 'IT']:
                    match = next((c for c in latest_cutoffs if c.get('branch_code') == kb), None)
                    val = match.get('cutoffs', {}).get('OC', 0) if match else 0
                    cutoff_details[f"Cutoff {kb}"] = val
                    if val > 0:
                        total_c += val
                        count_c += 1
                
                if count_c > 0:
                    avg_cutoff = total_c / count_c
            else:
                 for kb in ['CSE', 'ECE', 'MECH', 'IT']:
                    cutoff_details[f"Cutoff {kb}"] = 0

            # Safe conversion for placement
            place_val = 0
            raw_placement = college.get('placement')
            if raw_placement:
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
                    if 'admission' in f or 'tuition' in f:
                        total_fee = int(f.get('admission', 0)) + int(f.get('tuition', 0))
                        if total_fee > 0:
                            fees = f"₹{total_fee:,}/yr"
                except:
                    pass

            # Calculate Scores
            quality_score = self._calculate_quality_score(place_val, avg_cutoff, college)
            match_score = self._calculate_match_score(cutoffs, user_mark, user_comm)

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
                "Quality Score": quality_score,
                "Match Score": match_score,
                **cutoff_details,
                "Website": college.get('website', 'N/A')
            })

        if comparison_data:
            df = pd.DataFrame(comparison_data)
            
            st.dataframe(
                df,
                column_config={
                    "College Name": st.column_config.TextColumn("College", width="large"),
                    "Placement %": st.column_config.ProgressColumn(
                        "Placement", format="%.1f%%", min_value=0, max_value=100
                    ),
                    "Quality Score": st.column_config.ProgressColumn(
                        "Quality Score", 
                        format="%.0f/100", 
                        min_value=0, 
                        max_value=100,
                        help="Composite score based on Placement (40%), Cutoff Strength (40%), and Infrastructure (20%)"
                    ),
                    "Match Score": st.column_config.ProgressColumn(
                        "Match Score", 
                        format="%.0f/100", 
                        min_value=0, 
                        max_value=100,
                        help=f"Likelihood of admission based on your mark ({user_mark}) vs college cutoffs."
                    ),
                    "Total Seats": st.column_config.NumberColumn("Total Seats"),
                    "Fees": st.column_config.TextColumn("Approx Fees"),
                    "Cutoff CSE": st.column_config.NumberColumn("CSE (OC)", format="%.2f"),
                    "Cutoff ECE": st.column_config.NumberColumn("ECE (OC)", format="%.2f"),
                    "Website": st.column_config.LinkColumn("Link"),
                },
                use_container_width=True,
                hide_index=True
            )
            
            with st.expander("Detailed Comparison View"):
                st.table(df.set_index("College Name").T)
            
            st.divider()
            st.subheader("📊 Analytical Comparison")
            
            import plotly.graph_objects as go
            categories = ['Quality Score', 'Match Score', 'Placement %', 'Academic Strength']
            
            fig = go.Figure()
            for item in comparison_data:
                # Normalize values for radar
                q_score = item.get('Quality Score', 0)
                m_score = item.get('Match Score', 0)
                p_score = item.get('Placement %', 0)
                
                # Academic Strength derived from Cutoff (150-200 range -> 0-100)
                avg_c = (item.get('Cutoff CSE', 0) + item.get('Cutoff ECE', 0)) / 2
                if avg_c == 0: avg_c = 150
                a_score = max(0, min(100, (avg_c - 140) * 1.6)) # Scale 140-200 to 0-100 approx
                
                values = [q_score, m_score, p_score, a_score]
                fig.add_trace(go.Scatterpolar(
                    r=values, theta=categories, fill='toself', name=item.get('College Name')
                ))
                
            fig.update_layout(polar=dict(radialaxis=dict(visible=True, range=[0, 100])), height=400)
            st.plotly_chart(fig, use_container_width=True)

    def _calculate_quality_score(self, placement_pct, avg_cutoff, college):
        """
        Calculates a composite quality score (0-100).
        - Placement: 40%
        - Academic Strength (Cutoff): 40%
        - Infrastructure/Status: 20%
        """
        # 1. Placement Score (40 pts max)
        p_score = (placement_pct / 100) * 40
        
        # 2. Academic Score (40 pts max)
        # Map cutoff 150-200 to 0-40 pts
        # If cutoff < 150, score is minimal
        if avg_cutoff < 140:
            a_score = 5 # baseline
        else:
            # Range 140 to 200 is 60 points range. We map to 40 pts.
            a_score = ((avg_cutoff - 140) / 60) * 40
            a_score = max(0, min(40, a_score))
            
        # 3. Infra Score (20 pts max)
        i_score = 0
        if college.get('is_autonomous'): i_score += 10
        if college.get('has_hostel'): i_score += 5
        # City tier bonus
        major = ['CHENNAI', 'COIMBATORE', 'MADURAI', 'TRICHY']
        if any(c in str(college.get('district', '')).upper() for c in major):
            i_score += 5
        i_score = min(20, i_score)
        
        return round(p_score + a_score + i_score, 1)

    def _calculate_match_score(self, cutoffs, user_mark, user_comm):
        """
        Calculates admission probability score (0-100).
        Based on max cutoff for user's community across major branches.
        """
        if not cutoffs or user_mark == 0:
            return 0
            
        # Find minimum cutoff for this college for user's community (easiest branch to get?)
        # Or should we look at average? Let's look at a representative branch like ECE/CSE
        # Actually, let's take the MEDIAN cutoff for the user's community to represent "getting in".
        
        comm_cutoffs = []
        latest_year = max(c['year'] for c in cutoffs)
        for c in cutoffs:
            if c['year'] == latest_year:
                val = c.get('cutoffs', {}).get(user_comm, 0)
                if val and val > 0:
                    comm_cutoffs.append(val)
        
        if not comm_cutoffs:
            return 0
            
        # Use average of all branches to gauge difficulty
        college_avg = sum(comm_cutoffs) / len(comm_cutoffs)
        
        diff = user_mark - college_avg
        
        # Scoring Logic:
        # If user_mark >= college_avg + 5: 100% (Safe)
        # If user_mark == college_avg: 75% (Likely)
        # If user_mark == college_avg - 5: 40% (Risky)
        # If user_mark < college_avg - 20: 0%
        
        # Linear map: -20 to +10 -> 0 to 100
        # diff = -20 -> score 0
        # diff = +10 -> score 100
        
        score = ((diff + 20) / 30) * 100
        return round(max(0, min(100, score)), 1)
