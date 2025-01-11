from flask import Flask, jsonify, request, abort
import json
import os

app = Flask(__name__)

# Define your API key
API_KEY = "mysecureapikey123"

# Paths to JSON files
REGION_PATH = "json"  # Directory containing region JSON files
MOVIE_FILE = "json/movies.json"  # File containing movie details

# Middleware to check API key
@app.before_request
def verify_api_key():
    api_key = request.args.get('api_key')
    if api_key != API_KEY:
        abort(401, description="Unauthorized: Invalid API key")

# Load movie data once at startup
with open(MOVIE_FILE, 'r') as f:
    movies_data = json.load(f)["movies"]

@app.route('/movies', methods=['GET'])
def get_all_movies():
    """
    Fetches all movies with full details.
    """
    return jsonify({"movies": movies_data})

@app.route('/movies/<movie_name>', methods=['GET'])
def get_movie_by_name(movie_name):
    """
    Fetches details of a specific movie by name.
    """
    movie_name = movie_name.replace("%20", " ")
    for movie in movies_data:
        if movie["title"].lower() == movie_name.lower():
            return jsonify(movie)
    abort(404, description="Movie not found")

@app.route('/movies/<movie_name>/<region>', methods=['GET'])
def get_movie_by_name_and_region(movie_name, region):
    """
    Fetches details of a specific movie for a given region.
    """
    movie_name = movie_name.replace("%20", " ")
    region = region.lower()

    # Fetch the movie details
    movie = next((m for m in movies_data if m["title"].lower() == movie_name.lower()), None)
    if not movie:
        abort(404, description="Movie not found")

    # Verify if the movie is available in the region
    if region.capitalize() not in movie["regions"]:
        abort(404, description=f"Movie '{movie_name}' not available in region '{region}'")

    # Fetch region data
    region_file = f"{region}.json"
    region_file_path = os.path.join(REGION_PATH, region_file)
    if not os.path.exists(region_file_path):
        abort(404, description=f"Region '{region}' not found")

    with open(region_file_path, 'r') as f:
        region_data = json.load(f)

    # Response data
    response = {
        "movie": movie,
        "region": region_data["region"],
        "sub_cities": region_data.get("sub_cities", []),
        "cinemas": region_data.get("cinemas", [])
    }
    return jsonify(response)

@app.route('/movies/<movie_name>/<region>/<sub_city>', methods=['GET'])
def get_movie_by_name_region_sub_city(movie_name, region, sub_city):
    """
    Fetches details of a specific movie for a given region and sub-city.
    """
    movie_name = movie_name.replace("%20", " ")
    region = region.lower()
    sub_city = sub_city.lower()

    # Fetch the movie details
    movie = next((m for m in movies_data if m["title"].lower() == movie_name.lower()), None)
    if not movie:
        abort(404, description="Movie not found")

    # Verify if the movie is available in the region
    if region.capitalize() not in movie["regions"]:
        abort(404, description=f"Movie '{movie_name}' not available in region '{region}'")

    # Fetch region data
    region_file = f"{region}.json"
    region_file_path = os.path.join(REGION_PATH, region_file)
    if not os.path.exists(region_file_path):
        abort(404, description=f"Region '{region}' not found")

    with open(region_file_path, 'r') as f:
        region_data = json.load(f)

    # Verify if the sub-city exists
    if "sub_cities" in region_data and sub_city not in [sc.lower() for sc in region_data["sub_cities"]]:
        abort(404, description=f"Sub-city '{sub_city}' not found in region '{region}'")

    # Filter cinemas based on sub-city
    cinemas = [
        cinema for cinema in region_data.get("cinemas", [])
        if cinema.get("sub_city", "").lower() == sub_city
    ]

    if not cinemas:
        abort(404, description=f"No cinemas found in sub-city '{sub_city}'")

    # Response data
    response = {
        "movie": movie,
        "region": region_data["region"],
        "sub_city": sub_city.capitalize(),
        "cinemas": cinemas
    }
    return jsonify(response)

if __name__ == '__main__':
    os.makedirs(REGION_PATH, exist_ok=True)
    app.run(debug=True,host="0.0.0.0", port=5001)
