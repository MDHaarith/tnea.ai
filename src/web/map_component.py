
import folium
from folium.plugins import MarkerCluster
from streamlit_folium import st_folium
import streamlit as st

class MapComponent:
    def __init__(self, data_engine):
        self.data_engine = data_engine

    def render_map(self, colleges, center_lat=11.1271, center_lon=78.6569, zoom=7, user_location=None):
        """
        Renders a map with clustered markers.
        Optional: user_location = (lat, lon) to show user position and lines.
        """
        if not colleges:
            st.warning("No colleges to display on map.")
            return

        m = folium.Map(location=[center_lat, center_lon], zoom_start=zoom)
        
        # User Marker
        if user_location:
            folium.Marker(
                user_location,
                popup="Your Location",
                icon=folium.Icon(color='black', icon='home', prefix='fa'),
                tooltip="You are here"
            ).add_to(m)

        # Use MarkerCluster for colleges
        marker_cluster = MarkerCluster().add_to(m)

        valid_markers = 0
        for college in colleges:
            lat = college.get('lat')
            lon = college.get('lng')
            name = college.get('name', 'Unknown College')
            district = college.get('district', 'Unknown District')
            code = college.get('code', 'N/A')
            
            # Determine Color
            color = "blue"
            placement = college.get('placement')
            if placement and str(placement).replace('.', '', 1).isdigit():
                p_val = float(placement)
                if p_val > 90: color = "green"
                elif p_val > 75: color = "orange"
                else: color = "red"
            
            # Distance logic
            dist_str = ""
            if user_location and lat and lon:
                # Simple Euclidean approx sufficient for UI or handle better if needed
                # For now just use the line, exact km calculation can happen in popup if passed
                pass

            # Rich Popup Content
            popup_html = f"""
            <div style="width: 200px;">
                <b>{name}</b><br>
                <small>Code: {code}</small><br>
                <hr style="margin: 5px 0;">
                📍 {district}<br>
                💼 Placement: {placement if placement else 'N/A'}%
            </div>
            """

            if lat and lon:
                try:
                    folium.Marker(
                        [float(lat), float(lon)],
                        popup=folium.Popup(popup_html, max_width=250),
                        tooltip=f"{name} ({district})",
                        icon=folium.Icon(color=color, icon="info-sign")
                    ).add_to(marker_cluster)
                    
                    # Draw visual line if user location exists and few colleges
                    if user_location and len(colleges) <= 15:
                        folium.PolyLine(
                            [user_location, (float(lat), float(lon))],
                            color='gray',
                            weight=1,
                            opacity=0.5,
                            dash_array='5, 10'
                        ).add_to(m)
                        
                    valid_markers += 1
                except (ValueError, TypeError):
                    continue
        
        if valid_markers > 0:
            st_folium(m, width=800, height=500, use_container_width=True)
        else:
            st.info("No location data available for these colleges.")
