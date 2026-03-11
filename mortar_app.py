import streamlit as st
import math

# Updated firing tables with Time of Flight (sec) - sourced from Arma Reforger in-game data
firing_tables = [
    # Ring 0 (Disp 6m)
    {50: (1540, 13.2), 100: (1479, 13.2), 150: (1416, 13.0), 200: (1350, 12.8),
     250: (1279, 12.6), 300: (1201, 12.3), 350: (1106, 11.7), 400: (955, 10.7)},
    # Ring 1 (Disp 14m)
    {100: (1547, 20.0), 200: (1492, 19.9), 300: (1437, 19.7), 400: (1378, 19.5),
     500: (1317, 19.2), 600: (1249, 18.8), 700: (1174, 18.3), 800: (1085, 17.5),
     900: (954, 16.1)},
    # Ring 2 (Disp 24m)
    {200: (1538, 26.6), 300: (1507, 26.5), 400: (1475, 26.4), 500: (1443, 26.3),
     600: (1410, 26.2), 700: (1376, 26.0), 800: (1341, 25.8), 900: (1305, 25.5),
     1000: (1266, 25.2), 1100: (1225, 24.9), 1200: (1180, 24.4), 1300: (1132, 23.9),
     1400: (1076, 23.2), 1500: (1009, 22.3), 1600: (912, 20.9)},
    # Ring 3 (Disp 32m)
    {300: (1534, 31.7), 400: (1511, 31.6), 500: (1489, 31.6), 600: (1466, 31.5),
     700: (1442, 31.4), 800: (1419, 31.3), 900: (1395, 31.1), 1000: (1370, 31.0),
     1100: (1344, 30.8), 1200: (1318, 30.6), 1300: (1291, 30.3), 1400: (1263, 30.1),
     1500: (1233, 29.8), 1600: (1202, 29.4), 1700: (1169, 29.0), 1800: (1133, 28.5),
     1900: (1094, 28.0), 2000: (1051, 27.3), 2100: (999, 26.5), 2200: (931, 25.3),
     2300: (801, 22.7)},
    # Ring 4 (Disp 42m)
    {400: (1531, 36.3), 500: (1514, 36.2), 600: (1496, 36.2), 700: (1478, 36.1),
     800: (1460, 36.0), 900: (1442, 35.9), 1000: (1424, 35.8), 1100: (1405, 35.7),
     1200: (1385, 35.6), 1300: (1366, 35.4), 1400: (1346, 35.3), 1500: (1326, 35.1),
     1600: (1305, 34.9), 1700: (1283, 34.6), 1800: (1261, 34.4), 1900: (1238, 34.1),
     2000: (1214, 33.8), 2100: (1188, 33.5), 2200: (1162, 33.1), 2300: (1134, 32.7),
     2400: (1104, 32.2), 2500: (1070, 31.7), 2600: (1034, 31.0), 2700: (993, 30.3),
     2800: (942, 29.2), 2900: (870, 27.7)}
]

def calculate_mortar_adjustment(own_grid, target_grid, delta_elevation_m=0):
    x_own = int(own_grid[:3]) * 10
    y_own = int(own_grid[3:]) * 10
    x_target = int(target_grid[:3]) * 10
    y_target = int(target_grid[3:]) * 10
    
    delta_x = x_target - x_own
    delta_y = y_target - y_own
    range_m = math.sqrt(delta_x**2 + delta_y**2)
    
    if range_m == 0:
        raise ValueError("You are standing on the target - no adjustment possible.")
    
    # Bearing in mils
    bearing_deg = (90 - math.degrees(math.atan2(delta_y, delta_x))) % 360
    direction_mils = round(bearing_deg * (6400 / 360))
    
    # Find ring + table
    ring = None
    table = None
    for r in range(len(firing_tables)):
        tbl = firing_tables[r]
        if min(tbl.keys()) <= range_m <= max(tbl.keys()):
            ring = r
            table = tbl
            break
    
    if ring is None:
        raise ValueError(f"Range {range_m:.0f}m is out of mortar range (50-2900m).")
    
    # Interpolate elevation and TOF
    ranges = sorted(table.keys())
    for i in range(len(ranges) - 1):
        r1 = ranges[i]
        r2 = ranges[i + 1]
        if r1 <= range_m <= r2:
            elev1, tof1 = table[r1]
            elev2, tof2 = table[r2]
            fraction = (range_m - r1) / (r2 - r1)
            elevation_mils = elev1 + fraction * (elev2 - elev1)
            time_of_flight = tof1 + fraction * (tof2 - tof1)
            break
    else:
        elevation_mils, time_of_flight = table[range_m]
    
    elevation_mils = round(elevation_mils)
    time_of_flight = round(time_of_flight, 1)
    
    # Site correction for height
    site_deg = math.degrees(math.atan(delta_elevation_m / range_m))
    site_mils = round(site_deg * (6400 / 360))
    adjusted_elevation_mils = round(elevation_mils + site_mils)
    
    return {
        "direction_mils": direction_mils,
        "elevation_mils": adjusted_elevation_mils,
        "rings": ring,
        "range_m": round(range_m),
        "time_of_flight_sec": time_of_flight,
        "site_correction_mils": site_mils,
        "elevation_diff_m": delta_elevation_m
    }

# For standalone use
if __name__ == "__main__":
    own = input("Enter your 6-digit grid: ").strip()
    target = input("Enter target 6-digit grid: ").strip()
    delta_str = input("Enter elevation difference in meters (positive = target higher): ").strip()
    delta = int(delta_str) if delta_str.lstrip("-").isdigit() else 0
    
    result = calculate_mortar_adjustment(own, target, delta)
    print("\nMortar Adjustment Information:")
    print(f"Direction: {result['direction_mils']} mils")
    print(f"Adjusted Elevation: {result['elevation_mils']} mils")
    print(f"Rings: {result['rings']}")
    print(f"Horizontal Range: {result['range_m']} m")
    print(f"Time of Flight: {result['time_of_flight_sec']} seconds")
    print(f"Elevation difference: {result['elevation_diff_m']} m")
    print(f"Site correction applied: {result['site_correction_mils']} mils")

st.title("Arma Reforger Mortar Calculator")
st.markdown("Enter your grids (6-digit) and elevation difference. Positive = target higher.")

col1, col2 = st.columns(2)
with col1:
  own_grid = st.text_input("Your grid (e.g., 594138)", max_chars=6)
with col2:
  target_grid = st.text_input("Target grid (e.g., 625295)", max_chars=6)

  delta_elevation = st.number_input("Elevation diff (m) — positive = target higher", value=0, step=1)

if st.button("Calculate Mortar Adjustment"):
  if not own_grid or not target_grid or len(own_grid) != 6 or len(target_grid) != 6:
    st.error("Please enter valid 6-digit grids.")
else:
  try:
    result = calculate_mortar_adjustment(own_grid, target_grid, delta_elevation)

    st.success("Mortar Adjustment Information:")
    st.markdown(f"**Direction:** {result['direction_mils']} mils")
    st.markdown(f"**Adjusted Elevation:** {result['elevation_mils']} mils")
    st.markdown(f"**Rings / Charge:** {result['rings']}")
    st.markdown(f"**Horizontal Range:** {result['range_m']} m")
    st.markdown(f"**Time of Flight:** {result['time_of_flight_sec']} seconds")
    st.markdown(f"**Elevation difference:** {result['elevation_diff_m']} m")
    st.markdown(f"**Site correction applied:** {result['site_correction_mils']} mils")

    st.info("Assumes flat/no wind. Adjust manually in-game if needed.")
except ValueError as e:
  st.error(str(e))

  result = calculate_mortar_adjustment(own, target, delta)
  print("\nMortar Adjustment Information:")
  print(f"Direction: {result['direction_mils']} mils")
  print(f"Adjusted Elevation: {result['elevation_mils']} mils")
  print(f"Rings: {result['rings']}")
  print(f"Horizontal Range: {result['range_m']} m")
  print(f"Time of Flight: {result['time_of_flight_sec']} seconds")
  print(f"Elevation difference: {result['elevation_diff_m']} m")
  print(f"Site correction applied: {result['site_correction_mils']} mils")
