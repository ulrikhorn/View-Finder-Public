from flask import Flask, jsonify, render_template, request
import pandas as pd
from process_data import process_elevation_data  # Import the function from app2.py
app = Flask(__name__)



@app.route('/')  # Define a route for the root URL
def index():
    return render_template('3d_map_optimized.html') # Replace 'your_html_file.html'


clicked_latitude = None
clicked_longitude = None
current_lonlat_list = [[60.317979, 9.396161]]

@app.route('/receive_map_click', methods=['POST'])
def receive_map_click():
    global clicked_latitude
    global clicked_longitude
    global current_lonlat_list

    if request.is_json:
        data = request.get_json()
        print("Received map click data from browser:", data)

        clicked_latitude = data.get('latitude')
        clicked_longitude = data.get('longitude')
        
    
        print(f"Clicked at Latitude: {current_lonlat_list}, Longitude: {clicked_longitude}")

        # Process the coordinates as needed in your Flask application
        # For example, you could store them in a database, trigger another process, etc.

        return jsonify({"message": "Map click data received successfully"}), 200
    else:
        return jsonify({"error": "Request must be JSON"}), 400




@app.route('/get_coordinates')
def get_dataframe_json():
    current_lonlat_list = process_elevation_data(start_lat = clicked_latitude, start_lon = clicked_longitude, radius = 0.005, range_value = 0.5, angle_interval = 10)
    return jsonify(current_lonlat_list)

if __name__ == '__main__':
    #from waitress import serve
    #serve(app, host="0.0.0.0", port=8080)          # change this if going render
    app.run(debug=True)