from flask import Flask, render_template, request
import pandas as pd
import math
import numpy as np
import folium
from geopy import distance
from ielevation3 import get_elevation_data
import time


app = Flask(__name__)


def process_elevation_data(start_lat, start_lon, radius=0.005, range_value=0.5, angle_interval=10):
    start_time = time.time()
    df = get_elevation_data(start_lat, start_lon, r_value=radius, range_value=range_value, angle_interval=angle_interval)
    no_angles = len(df) / (range_value / radius) # calculating number of angles based on the range outwards and the interval between each point (radius)
    angles = list(np.arange(0, no_angles, 1)) * int(len(df) / no_angles)
    
    iterations = np.array([np.arange(0, len(df) / no_angles)])
    iterations = np.repeat(iterations, no_angles)
    
    df = df.assign(angle_nr=angles)
    df = df.assign(iteration=iterations)

    initial_elevation = int(df.iloc[0]['elevation'])

    df['nr'] = range(len(df))
    df = df.set_index('nr')

    dist_list = []
    for i in range(len(df)):
        point1 = (df.loc[1]['lat'], df.loc[1]['lon'])
        point2 = (df.loc[i]['lat'], df.loc[i]['lon'])
        dist = distance.geodesic(point1, point2, ellipsoid='GRS-80').m
        dist_list.append(dist)

    df = df.assign(distance_to_start=dist_list)

    def distance_to_horizon(height): # height in km
        r = 6371000 # Radius of the earth in m
        a = math.sqrt((r+height)**2 - r**2)
        return a
    
    def height_loss_curvature(distance_to_start, distance_to_horizon):
        r = 6371000 # Radius of the earth in m
        x = math.sqrt(distance_to_horizon**2 - 2*distance_to_horizon*distance_to_start + distance_to_start**2 + r**2) - r
        return x
    
    #df['elevation'] = df['elevation'] - height_loss_curvature(df['distance_to_start'], distance_to_horizon(df['elevation']))
    distance_to_horizon_vector = distance_to_horizon(initial_elevation)
    df['distance_to_horizon'] = distance_to_horizon_vector
    #df['distance_to_horizon'] = df.apply(lambda row: distance_to_horizon(initial_elevation), axis=1)

    df['curvature_loss'] = df.apply(lambda row: height_loss_curvature(row['distance_to_start'], row['distance_to_horizon']), axis=1)

    #df['elevation'].iloc[72:] = df[72:].apply(lambda row: row['elevation'] - height_loss_curvature(row['distance_to_start'], distance_to_horizon(row['elevation'])), axis=1)
    #df['elevation'] = df[72:].apply(lambda row: row['elevation'] - height_loss_curvature(row['distance_to_start'], distance_to_horizon(row['elevation'])), axis=1)

    #print(df)
    df = df.assign(lower=['true' if i < initial_elevation else 'false' for i in df['elevation']])
    #df['lower'] = np.where(df['elevation'] < initial_elevation, 'true', 'false')
    df.loc[:no_angles-1, 'lower'] = 'start' # value spesific
    
    
    height_diff = []
    for i in range(len(df)):
        elev_diff = df.loc[i]['elevation'] - df.loc[1]['elevation']
        height_diff.append(elev_diff)

    df = df.assign(elev_diff=height_diff)

    hypotenuse = []
    for i in range(len(df)):
        kat1 = df.loc[i]['elev_diff']
        kat2 = df.loc[i]['distance_to_start']

        kat1 = float(kat1)
        kat2 = float(kat2)
        hyp = math.sqrt((kat1**2) + (kat2**2))
        if df.loc[i]['elev_diff'] > 0:
            hypotenuse.append(hyp)
        else:
            hypotenuse.append(0)

    df = df.assign(hyp=hypotenuse)

    df['angle'] = np.arcsin(df['elev_diff'] / df['hyp'])

    def height_at(dist_to_start, angle_at_query):
        c = (dist_to_start / math.cos(angle_at_query))
        height = math.sqrt((c**2) - (dist_to_start**2))
        return height

    df = df.rename(columns={'Unnamed: 0': 'nr1'})
    df['nr'] = range(len(df))

    df['highest_seen'] = 'FALSE'
    df['seen'] = 'FALSE'
    #print(len(df['angle_nr']))
    for i in np.unique(df['angle_nr']):
        direction_df = df[df['angle_nr'] == i]
        print(i)
        highest_seen_nr = []
        highest_seen = None
        if direction_df.loc[direction_df['lower'] == 'false'].empty: # if all points in one direction are lower # add in condition that the points are not byond the horizon
            #df = df.loc[df['angle_nr'] == i].assign(seen=['true' if i < distance_to_horizon else 'false' for i in direction_df['distance_to_start']])
            df.loc[df['angle_nr'] == i, 'seen'] = "true"
            continue

        #if direction_df.loc[direction_df['lower'] == 'false'].empty:
            # Check for rows where distance_to_start < distance_to_horizon
            condition = (df['angle_nr'] == i) & (df['distance_to_start'] < df['distance_to_horizon'])

            # Update 'seen' to "true" only for rows that meet the condition
            df.loc[condition, 'seen'] = "true"

            # Rows where the condition is false will remain unchanged.
            continue    
        else:
            highest_seen_nr = direction_df.loc[direction_df['lower'] == 'false', 'nr'].iloc[0]
            highest_seen = df.query(f'nr == {highest_seen_nr}')

        for j in np.unique(direction_df['iteration']):
            if int(j) < len(iterations):
                query_itt = df.query(f'angle_nr == {i} & iteration == {j}')
                
                if int(query_itt['iteration'].iloc[0]) == 0:
                    df.loc[query_itt.index, 'seen'] = "true"
                    continue
                else:
                    if query_itt['lower'].iloc[0] == 'true' and int(j) < int(highest_seen['iteration'].iloc[0]):
                        df.loc[query_itt.index, 'seen'] = "true"
                        continue
                    else:
                        if int(query_itt['nr'].iloc[0]) == int(highest_seen['nr'].iloc[0]):
                            df.loc[query_itt.index, 'seen'] = "true"
                            continue
                        else:
                            if query_itt['lower'].iloc[0] == 'false':
                                if int(query_itt['elevation'].iloc[0]) > int(highest_seen['elevation'].iloc[0]):
                                    if height_at(float(highest_seen['distance_to_start'].iloc[0]), float(query_itt['angle'].iloc[0])) > int(highest_seen['elev_diff'].iloc[0]):
                                        highest_seen = query_itt

        if highest_seen is not None:
            df.loc[highest_seen.index, 'highest_seen'] = "true"

    #df.to_csv("elevation_data.csv", index=False) #Optional saving to csv.

    latlon = []
    unique_angles = df['angle_nr'].unique()
    for angle in unique_angles:
        angle_df = df[df['angle_nr'] == angle]
        highest_seen_points = angle_df[angle_df['highest_seen'] == 'true']

        if not highest_seen_points.empty:
            # If there's a highest_seen point, use it
            latlon.append([highest_seen_points.iloc[0]['lat'], highest_seen_points.iloc[0]['lon'], angle])
        else:
            # If no highest_seen, use the point with the highest iteration
            filtered_df = angle_df[angle_df['distance_to_start'] < angle_df['distance_to_horizon']]
            max_iteration_point = filtered_df.loc[filtered_df['iteration'].idxmax()]
            #max_iteration_point = angle_df.loc[angle_df['iteration'].idxmax()]
            latlon.append([max_iteration_point['lat'], max_iteration_point['lon'], angle])


    latlon = sorted(latlon, key=lambda x: x[2])
    latlon = [sublist[:2] for sublist in latlon]
    latlon.append(latlon[0])

    mapit = folium.Map(location=latlon[0], zoom_start=12, tiles='https://{s}.tile.opentopomap.org/{z}/{x}/{y}.png', attr="test")
    #for coord in latlon[:-1]:
        #folium.Marker(location=[coord[0], coord[1]], fill_color='#43d9de', radius=8).add_to(mapit)

    #folium.Marker(location=[start_lat, start_lon], icon=folium.Icon(color="red"), radius=8).add_to(mapit)

    folium.PolyLine(locations=latlon, color='blue', weight=5).add_to(mapit)
    print("--- %s seconds ---" % (time.time() - start_time))
    return mapit._repr_html_()

@app.route('/', methods=['GET', 'POST'])
def index():
    initial_map = folium.Map(location=[59.976654, 10.671793], zoom_start=10, tiles='https://{s}.tile.opentopomap.org/{z}/{x}/{y}.png', attr="test")
    initial_map_html = initial_map._repr_html_()

    if request.method == 'POST':
        try:
            start_lat = float(request.form['start_lat'])
            start_lon = float(request.form['start_lon'])
            radius = float(request.form['radius'])
            map_html = process_elevation_data(start_lat, start_lon, radius)
            return render_template('index.html', map_html=map_html, initial_map_html=initial_map_html)
        except ValueError:
            return render_template('index.html', error="Invalid input. Please enter valid numbers.", initial_map_html=initial_map_html)
    
    return render_template('index.html', initial_map_html=initial_map_html)


if __name__ == '__main__':
    #from waitress import serve
    #serve(app, host="0.0.0.0", port=8080)          # change this if going render
    app.run(debug=True)
