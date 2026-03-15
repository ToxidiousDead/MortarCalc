import streamlit as st
import math

if 'last_result' not in st.session_state:
    st.session_state.last_result = None
if 'last_own_grid' not in st.session_state:
    st.session_state.last_own_grid = ""
if 'last_target_grid' not in st.session_state:
    st.session_state.last_target_grid = ""
if 'last_delta_elevation' not in st.session_state:
    st.session_state.last_delta_elevation = 0
if 'last_faction' not in st.session_state:
    st.session_state.last_faction = ""
if 'last_shell_type' not in st.session_state:
    st.session_state.last_shell_type = ""

def calculate_mortar_adjustment(own_grid, target_grid, delta_elevation_m=0, firing_tables=None):
    if firing_tables is None or not firing_tables:
        raise ValueError("No valid firing tables for the selected faction and shell type.")
    
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
        min_r = min(tbl.keys())
        max_r = max(tbl.keys())
        if min_r <= range_m <= max_r:
            ring = r
            table = tbl
            break
   
    if ring is None:
        raise ValueError(f"Range {range_m:.0f}m is out of range for this shell (check selected faction/shell).")
   
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

# Mortar tables dictionary - US HE is your original; others are placeholders
# Fill placeholders with real in-game values (from ballistic manual screenshots or testing)
mortar_tables = {
    "US": {
        "HE": [  # Your full original US M252 HE tables (paste the complete list here)
            # Ring 0 (Disp 6m)
            {50: (1540, 13.2), 100: (1479, 13.2), 150: (1416, 13.0), 200: (1350, 12.8),
             250: (1279, 12.6), 300: (1201, 12.3), 350: (1106, 11.7), 400: (955, 10.7)},
            # Ring 1 (Disp 14m)
            {100: (1547, 20.0), 200: (1492, 19.9), 300: (1437, 19.7), 400: (1378, 19.5),
             500: (1317, 19.2), 600: (1249, 18.8), 700: (1174, 18.3), 800: (1085, 17.5),
             900: (954, 16.1)},
            # Ring 2 (Disp 24m) - paste full from your code
            {200: (1538, 26.6), 300: (1507, 26.5), 400: (1475, 26.4), 500: (1443, 26.3),
             600: (1410, 26.2), 700: (1376, 26.0), 800: (1341, 25.8), 900: (1305, 25.5),
             1000: (1266, 25.2), 1100: (1225, 24.9), 1200: (1180, 24.4), 1300: (1132, 23.9),
             1400: (1076, 23.2), 1500: (1009, 22.3), 1600: (912, 20.9)},
            # Ring 3 (Disp 32m) - paste full
            {300: (1534, 31.7), 400: (1511, 31.6), 500: (1489, 31.6), 600: (1466, 31.5),
             700: (1442, 31.4), 800: (1419, 31.3), 900: (1395, 31.1), 1000: (1370, 31.0),
             1100: (1344, 30.8), 1200: (1318, 30.6), 1300: (1291, 30.3), 1400: (1263, 30.1),
             1500: (1233, 29.8), 1600: (1202, 29.4), 1700: (1169, 29.0), 1800: (1133, 28.5),
             1900: (1094, 28.0), 2000: (1051, 27.3), 2100: (999, 26.5), 2200: (931, 25.3),
             2300: (801, 22.7)},
            # Ring 4 (Disp 42m) - paste full "Range: (Elevation, Time of flight)"
            {400: (1531, 36.3), 500: (1514, 36.2), 600: (1496, 36.2), 700: (1478, 36.1),
             800: (1460, 36.0), 900: (1442, 35.9), 1000: (1424, 35.8), 1100: (1405, 35.7),
             1200: (1385, 35.6), 1300: (1366, 35.4), 1400: (1346, 35.3), 1500: (1326, 35.1),
             1600: (1305, 34.9), 1700: (1283, 34.6), 1800: (1261, 34.4), 1900: (1238, 34.1),
             2000: (1214, 33.8), 2100: (1188, 33.5), 2200: (1162, 33.1), 2300: (1134, 32.7),
             2400: (1104, 32.2), 2500: (1070, 31.7), 2600: (1034, 31.0), 2700: (993, 30.3),
             2800: (942, 29.2), 2900: (870, 27.7)}
        ],
        "Smoke": [
            # Ring 0 - 1 Ring table (lowest charge)
            {
                200: (1463, 17.7), 250: (1427, 17.6), 300: (1391, 17.5), 350: (1352, 17.3),
                400: (1314, 17.2), 450: (1271, 16.9), 500: (1227, 16.7), 550: (1178, 16.4),
                600: (1124, 15.4), 650: (1060, 14.7), 700: (982, 13.0), 750: (822, 12.5)},
            # Ring 1 - 2 Rings table
            {
                200: (1528, 24.8), 300: (1491, 24.7), 400: (1453, 24.6), 500: (1414, 24.4),
                600: (1374, 24.2), 700: (1333, 24.0), 800: (1289, 23.3), 900: (1242, 22.9),
                1000: (1191, 22.3), 1100: (1133, 21.6), 1200: (1067, 20.5), 1300: (980, 18.0),
                1400: (818, 16.0)},
            # Ring 2 - 3 Rings table
            {
                300: (1522, 29.6), 400: (1495, 29.6), 500: (1468, 29.5), 600: (1440, 29.3), 700: (1412, 29.2),
                800: (1383, 29.0), 900: (1354, 28.9), 1000: (1323, 28.6), 1100: (1291, 28.4), 1200: (1257, 27.7),
                1300: (1221, 27.3), 1400: (1183, 26.8), 1500: (1142, 26.2), 1600: (1096, 25.5), 1700: (1044, 24.5),
                1800: (980, 23.0), 1900: (892, 21.5)},
            # Ring 3 - 4 Rings table (highest charge)
            {
                400: (1517, 33.6), 500: (1495, 33.5), 600: (1474, 33.5), 700: (1452, 33.4), 800: (1429, 33.2),
                900: (1407, 33.1), 1000: (1383, 33.0), 1100: (1360, 32.8), 1200: (1335, 32.6), 1300: (1310, 32.4),
                1400: (1284, 32.1), 1500: (1257, 31.9), 1600: (1228, 31.5), 1700: (1199, 30.8), 1800: (1166, 30.3),
                1900: (1132, 29.8), 2000: (1096, 29.1), 2100: (1055, 28.4), 2200: (1008, 27.4), 2300: (952, 25.8),
                2400: (871, 25.8)}
        ],
        "Illumination": [
            # Ring 1 (1 Ring)
            {
                200: (1463, 18.1), 250: (1428, 18.0), 300: (1391, 17.9), 350: (1352, 17.7),
                400: (1312, 17.3), 450: (1271, 17.0), 500: (1227, 16.7), 550: (1178, 16.4),
                600: (1124, 15.4), 650: (1060, 14.7), 700: (982, 13.3), 750: (822, 12.0)
            },
            # Ring 2 (2 Rings)
            {
                200: (1529, 26.2), 300: (1493, 26.1), 400: (1457, 26.0), 500: (1419, 25.8),
                600: (1379, 25.6), 700: (1338, 25.4), 800: (1295, 25.1), 900: (1249, 24.7),
                1000: (1199, 24.3), 1100: (1081, 23.0), 1200: (1005, 22.0), 1300: (900, 20.5),
                1400: (818, 18.0)
            },
            # Ring 3 (3 Rings)
            {
                300: (1521, 31.1), 400: (1494, 31.1), 500: (1466, 31.0), 600: (1438, 30.8),
                700: (1409, 30.7), 800: (1380, 30.5), 900: (1349, 30.3), 1000: (1317, 29.8),
                1100: (1284, 29.4), 1200: (1249, 29.1), 1300: (1212, 28.6), 1400: (1172, 28.1),
                1500: (1128, 27.4), 1600: (1082, 26.6), 1700: (962, 25.6), 1800: (875, 24.1),
                1900: (875, 24.1)   # last entry not fully visible in photo – leave or fill from in-game if needed
            },
            # Ring 4 (4 Rings)
            {
                400: (1515, 35.7), 500: (1493, 35.7), 600: (1471, 35.5), 700: (1448, 35.4),
                800: (1426, 35.2), 900: (1402, 35.0), 1000: (1378, 34.8), 1100: (1353, 34.6),
                1200: (1328, 34.4), 1300: (1301, 34.1), 1400: (1274, 33.8), 1500: (1215, 33.4),
                1600: (1184, 33.2), 1700: (1151, 32.1), 1800: (1115, 31.5), 1900: (1076, 30.8),
                2000: (1033, 29.9), 2100: (985, 28.8), 2200: (928, 27.4), 2300: (855, 26.0),
                2400: (855, 27.4)   # last entry not fully visible in photo
            }
        ],  # Placeholder: limited rings, longer TOF for hang time
        "Training": [
            # Ring 0 (0 Rings)
            {
                50: (1540, 13.2), 100: (1479, 13.2), 150: (1417, 13.0), 200: (1350, 12.8),
                250: (1279, 12.6), 300: (1202, 12.3), 350: (1107, 11.7), 400: (958, 10.7)
            },
            # Ring 1 (1 Ring)
            {
                200: (1498, 20.4), 300: (1445, 20.3), 400: (1391, 20.1), 500: (1333, 19.8), 600: (1271, 19.4),
                700: (1204, 19.0), 800: (1124, 18.3), 900: (1023, 17.3), 1000: (812, 14.7)
            },
            # Ring 2 (2 Rings)
            {
                300: (1507, 26.5), 400: (1476, 26.4), 500: (1444, 26.3), 600: (1411, 26.0), 700: (1377, 25.8),
                800: (1345, 25.5), 900: (1305, 25.2), 1000: (1266, 24.9), 1100: (1225, 24.4), 1200: (1180, 24.0),
                1300: (1133, 23.2), 1400: (1078, 22.4), 1500: (1011, 20.9), 1600: (916, 20.9)
            },
            # Ring 3 (3 Rings)
            {
                400: (1511, 31.6), 500: (1489, 31.5), 600: (1466, 31.5), 700: (1442, 31.4), 800: (1419, 31.2),
                900: (1395, 31.1), 1000: (1370, 30.9), 1100: (1345, 30.7), 1200: (1318, 30.5), 1300: (1291, 30.3),
                1400: (1263, 30.0), 1500: (1233, 29.4), 1600: (1203, 29.0), 1700: (1169, 28.5), 1800: (1134, 28.0),
                1900: (1095, 27.6), 2000: (1051, 27.3), 2100: (1000, 26.5), 2200: (933, 25.3), 2300: (803, 22.7)
            },
            # Ring 4 (4 Rings)
            {
                500: (1512, 35.9), 600: (1494, 35.8), 700: (1476, 35.8), 800: (1458, 35.7), 900: (1439, 35.6),
                1000: (1420, 35.4), 1100: (1402, 35.3), 1200: (1382, 35.2), 1300: (1362, 35.0), 1400: (1342, 34.9),
                1500: (1321, 34.5), 1600: (1300, 34.2), 1700: (1277, 34.0), 1800: (1255, 33.7), 1900: (1231, 33.4),
                2000: (1206, 33.0), 2100: (1180, 32.7), 2200: (1153, 32.2), 2300: (1123, 31.7), 2400: (1092, 31.1),
                2500: (1058, 30.4), 2600: (1018, 29.5), 2700: (973, 28.4), 2800: (915, 26.1), 2900: (812, 26.1)
            }
        ],
    },
    "RU": {
        "HE": [  # Placeholder for 2B14 Podnos HE (max ~2300m)
            # Ring 1 (Первый / First charge)
            {
                100: (1446, 19.5), 200: (1392, 19.4), 300: (1335, 19.2), 400: (1275, 18.9),
                500: (1212, 18.6), 600: (1141, 18.1), 700: (1058, 17.4), 800: (952, 16.4)
            },
            # Ring 2 (Второй / Second charge)
            {
                200: (1432, 24.8), 300: (1397, 24.7), 400: (1362, 24.7), 500: (1325, 24.6),
                600: (1288, 24.2), 700: (1248, 24.0), 800: (1207, 23.7), 900: (1162, 23.3),
                1000: (1114, 22.9), 1100: (1060, 22.3), 1200: (997, 21.5), 1300: (914, 20.4),
                1400: (755, 17.8)
            },
            # Ring 3 (Третий / Third charge)
            {
                300: (1423, 28.9), 400: (1397, 28.9), 500: (1370, 28.8), 600: (1343, 28.6),
                700: (1315, 28.5), 800: (1286, 28.3), 900: (1257, 28.1), 1000: (1226, 27.9),
                1100: (1193, 27.6), 1200: (1159, 27.6), 1300: (1123, 27.2), 1400: (1084, 26.4),
                1500: (1040, 25.8), 1600: (991, 25.1), 1700: (932, 24.2), 1800: (851, 22.8)
            },
            # Ring 4 (Дальнобойный / Long-range / Fourth charge)
            {
                400: (1418, 32.9), 500: (1398, 32.9), 600: (1376, 32.8), 700: (1355, 32.7),
                800: (1335, 32.6), 900: (1311, 32.6), 1000: (1288, 32.2), 1100: (1264, 32.1),
                1200: (1240, 31.8), 1300: (1215, 31.6), 1400: (1189, 31.3), 1500: (1161, 31.0),
                1600: (1133, 30.7), 1700: (1102, 30.7), 1800: (1069, 29.8), 1900: (1034, 29.3),
                2000: (995, 28.7), 2100: (950, 27.9), 2200: (896, 26.9), 2300: (820, 25.3)
            }
        ],
        "Smoke": [
            # Ring 1 (ВТОРОЙ / Second)
            {200: (1381, 18.4), 300: (1319, 18.2), 400: (1252, 17.9), 500: (1179, 17.5),
             600: (1097, 16.9), 700: (993, 16.0), 800: (805, 13.9)},
            # Ring 2 (ТРЕТИЙ / Third)
            {300: (1387, 23.5), 400: (1348, 23.3), 500: (1308, 23.2), 600: (1266, 22.9),
             700: (1222, 22.7), 800: (1175, 22.3), 900: (1123, 21.8), 1000: (1065, 21.3),
             1100: (994, 20.4), 1200: (902, 19.2)},
            # Ring 3 (ДАЛЬНОБОЙНЫЙ / Long-range / Fourth)
            {400: (1387, 27.3), 500: (1357, 27.2), 600: (1327, 27.1), 700: (1296, 26.9),
             800: (1264, 26.7), 900: (1231, 26.7), 1000: (1196, 26.5), 1100: (1159, 25.8),
             1200: (1119, 25.4), 1300: (1075, 24.9), 1400: (1026, 24.3), 1500: (969, 23.5),
             1600: (896, 22.3), 1700: (753, 19.8)}
        ],  # Placeholder
        "Illumination": [
            # Ring 1 (ПЕРВЫЙ / First)
            {100: (1421, 16.4), 150: (1381, 16.3), 200: (1339, 16.2), 250: (1296, 16.1),
             300: (1251, 15.9), 350: (1203, 15.7), 400: (1151, 15.4), 450: (1093, 15.4),
             500: (1028, 14.5), 550: (945, 13.8), 600: (799, 12.3)},
            # Ring 2 (ВТОРОЙ / Second)
            {200: (1417, 23.6), 300: (1374, 23.5), 400: (1330, 23.3), 500: (1284, 23.1),
             600: (1234, 22.8), 700: (1182, 22.4), 800: (1124, 22.2), 900: (1057, 21.9),
             1000: (979, 21.3), 1100: (870, 18.9)},
            # Ring 3 (ТРЕТИЙ / Third)
            {300: (1411, 29.0), 400: (1381, 29.0), 500: (1348, 28.9), 600: (1315, 28.6),
             700: (1281, 28.4), 800: (1246, 28.1), 900: (1209, 27.8), 1000: (1170, 27.4),
             1100: (1128, 27.0), 1200: (1082, 26.5), 1300: (1031, 25.8), 1400: (973, 25.0),
             1500: (903, 23.9), 1600: (807, 22.3)},
            # Ring 4 (ДАЛЬНОБОЙНЫЙ / Long-range / Fourth)
            {400: (1411, 35.3), 500: (1388, 35.2), 600: (1364, 35.1), 700: (1341, 35.0),
             800: (1316, 34.8), 900: (1291, 34.8), 1000: (1265, 34.7), 1100: (1238, 34.2),
             1200: (1210, 33.9), 1300: (1181, 33.6), 1400: (1150, 33.2), 1500: (1119, 33.2),
             1600: (1085, 32.8), 1700: (1048, 31.8), 1800: (1009, 31.2), 1900: (965, 30.4),
             2000: (917, 29.6), 2100: (860, 28.4), 2200: (787, 26.9)}
        ]  # Placeholder
        # Training not typically available for RU in sources
    }
}

# UI
st.title("Arma Reforger Mortar Calculator")
st.markdown("Enter your grids (6-digit) and elevation difference. Positive = target higher.")

faction = st.selectbox("Mortar Faction", ["US (M252 81mm)", "RU (2B14 82mm)"], index=0)
shell_type = st.selectbox("Shell Type", ["HE", "Smoke", "Illumination", "Training"], index=0)

faction_key = "US" if faction.startswith("US") else "RU"

if selected_tables := mortar_tables.get(faction_key, {}).get(shell_type):
    max_r = max(max(tbl.keys()) for tbl in selected_tables if tbl)
    st.caption(f"Max range for {faction} - {shell_type}: ~{max_r}m")

col1, col2 = st.columns(2)
with col1:
    own_grid = st.text_input("Your grid (e.g., 594138)", max_chars=6)
with col2:
    target_grid = st.text_input("Target grid (e.g., 625295)", max_chars=6)

delta_elevation = st.number_input("Elevation diff (m) — positive = target higher", value=0, step=1)

if st.button("Calculate Mortar Adjustment"):
    if not own_grid or not target_grid or len(own_grid) != 6 or len(target_grid) != 6:
        st.error("Please enter valid 6-digit grids in both fields.")
    else:
        try:
            selected_tables = mortar_tables.get(faction_key, {}).get(shell_type, None)
            if selected_tables is None or len(selected_tables) == 0:
                st.error(f"Firing tables not yet available for {faction} - {shell_type}.")
            else:
                # Optional: quick range validity check (from earlier)
                approx_delta_x = int(target_grid[:3]) - int(own_grid[:3])
                approx_delta_y = int(target_grid[3:]) - int(own_grid[3:])
                approx_range = 10 * math.sqrt(approx_delta_x**2 + approx_delta_y**2)
                max_range = max(max(tbl.keys()) for tbl in selected_tables if tbl)
                if approx_range > max_range + 50:
                    st.error(f"Range ≈{approx_range:.0f}m exceeds max for this shell ({max_range}m).")
                else:
                    result = calculate_mortar_adjustment(own_grid, target_grid, delta_elevation, firing_tables=selected_tables)

                    st.session_state.last_result = result
                    st.session_state.last_own_grid = own_grid
                    st.session_state.last_target_grid = target_grid
                    st.session_state.last_delta_elevation = delta_elevation
                    st.session_state.last_faction = faction
                    st.session_state.last_shell_type = shell_type
                    
                    # Display result
                    st.success("Mortar Adjustment Information:")
                    st.markdown(f"**Faction / Shell:** {faction} - {shell_type}")
                    st.markdown(f"**Your grid:** {own_grid}")
                    st.markdown(f"**Target grid:** {target_grid}")
                    st.markdown(f"**Elevation diff:** {delta_elevation} m")
                    st.markdown(f"**Direction:** {result['direction_mils']} mils")
                    st.markdown(f"**Adjusted Elevation:** {result['elevation_mils']} mils")
                    st.markdown(f"**Rings / Charge:** {result['rings']}")
                    st.markdown(f"**Horizontal Range:** {result['range_m']} m")
                    st.markdown(f"**Time of Flight:** {result['time_of_flight_sec']} seconds")
                    st.markdown(f"**Site correction:** {result['site_correction_mils']} mils")
                    
                    st.info("Assumes flat terrain / no wind. Verify in-game.")
                    

                    # ── SAVE FEATURE ────────────────────────────────────────────────
                    # Initialize saved solutions in session state if not exists
                    if 'saved_solutions' not in st.session_state:
                        st.session_state.saved_solutions = []

                    # Button to trigger save
                    if st.button("💾 Save this solution for later"):
                        st.session_state.show_save_input = True

                    # Show input field only after button press
                    if 'show_save_input' in st.session_state and st.session_state.show_save_input:
                        save_name = st.text_input("Enter a name for this firing solution", placeholder="e.g. Enemy squad at hill 245")
                        col_save, col_cancel = st.columns(2)
                        with col_save:
                            if st.button("Confirm Save") and save_name.strip():
                                # Save the full context
                                saved_entry = {
                                    "name": save_name.strip(),
                                    "timestamp": st.session_state.get('last_calc_time', "now"),
                                    "own_grid": own_grid,
                                    "target_grid": target_grid,
                                    "delta_elevation": delta_elevation,
                                    "faction": faction,
                                    "shell_type": shell_type,
                                    "result": result
                                }
                                st.session_state.saved_solutions.append(saved_entry)
                                st.success(f"Saved as: **{save_name}**")
                                st.session_state.show_save_input = False  # hide input
                                st.rerun()  # refresh to show updated list
                        with col_cancel:
                            if st.button("Cancel"):
                                st.session_state.show_save_input = False
                                st.rerun()

                    # Show saved solutions
                    if st.session_state.get('show_save_input', False):
                        save_name = st.text_input("Enter a name for this firing solution", placeholder="e.g. Enemy squad at hill 245")
                        col_save, col_cancel = st.columns(2)
                        with col_save:
                            if st.button("Confirm Save") and save_name.strip():
                                saved_entry = {
                                    "name": save_name.strip(),
                                    "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M"),
                                    "own_grid": own_grid,
                                    "target_grid": target_grid,
                                    "delta_elevation": delta_elevation,
                                    "faction": faction,
                                    "shell_type": shell_type,
                                    "result": result
                                }
                                st.session_state.saved_solutions.append(saved_entry)
                                st.success(f"Saved as: **{save_name}**")
                                st.session_state.show_save_input = False
                                st.rerun()
                        with col_cancel:
                            if st.button("Cancel"):
                                st.session_state.show_save_input = False
                                st.rerun()

        except ValueError as e:
            st.error(str(e))
        except Exception as e:
            st.error(f"Calculation failed: {str(e)}")

# Optional: Auto-fill inputs if loaded from saved
if st.session_state.last_result:
    st.markdown("### Last Calculated Solution")
    st.markdown(f"**Faction / Shell:** {st.session_state.last_faction} - {st.session_state.last_shell_type}")
    st.markdown(f"**Elevation diff:** {st.session_state.last_delta_elevation} m")
    st.markdown(f"**Direction:** {st.session_state.last_result['direction_mils']} mils")
    st.markdown(f"**Adjusted Elevation:** {st.session_state.last_result['elevation_mils']} mils")
    st.markdown(f"**Rings / Charge:** {st.session_state.last_result['rings']}")
    st.markdown(f"**Horizontal Range:** {st.session_state.last_result['range_m']} m")
    st.markdown(f"**Time of Flight:** {st.session_state.last_result['time_of_flight_sec']} seconds")
    st.markdown("---")
