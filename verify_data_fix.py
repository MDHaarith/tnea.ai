
import sys
import os
import logging

# Add src to path
sys.path.append(os.path.join(os.getcwd(), 'src'))

from data.loader import DataEngine

# Config logging
logging.basicConfig(level=logging.INFO)

def verify_data():
    print("Initializing DataEngine...")
    engine = DataEngine()
    
    # Check CEG (Code 1)
    ceg = engine.get_college_by_code('1')
    if ceg:
        print(f"CEG (Code 1) Location: Lat={ceg.get('lat')}, Lng={ceg.get('lng')}")
        # Geo json has lat: "13.0122469", lon: "80.2347814"
        # Original json has lat: 13.0827, lng: 80.2707
        
        if abs(ceg.get('lat', 0) - 13.0122) < 0.01:
            print("✅ CEG Location updated correctly from geo_locations.json")
        else:
            print("❌ CEG Location NOT updated. Still using old or generic data.")
            
    # Check Seats
    seats = engine.get_total_seats_for_college('1')
    print(f"CEG Total Seats: {seats}")
    if seats > 0:
         print("✅ Seat calculation working")
    else:
         print("❌ Seat calculation failed (0 seats)")

if __name__ == "__main__":
    verify_data()
