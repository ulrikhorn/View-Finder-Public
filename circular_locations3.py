import pandas as pd
import numpy as np

def straightlines(start_lat, start_lon, r_value, range_value, angle_interval=5):
    df = pd.DataFrame({'lat': [], 'lon': []})

    for r in np.arange(0, range_value, r_value):
        angles = np.arange(angle_interval, 360+angle_interval, angle_interval)  # Angles every 1 degree. Every 5 degrees would be 5, 365, 5 or 1, 361, 1
        angles_rad = np.radians(angles)

        lon_list = start_lon + r * np.cos(angles_rad)
        lat_list = start_lat + r * np.sin(angles_rad)

        test_df = pd.DataFrame({'lat': lat_list, 'lon': lon_list})
        df = pd.concat([df, test_df], ignore_index=True)

    return df
