from flask import Flask, json, request, jsonify
from io import BytesIO
from PIL import Image
import base64
import numpy as np
from sklearn.cluster import KMeans
from sklearn.metrics import pairwise_distances_argmin
from collections import Counter

app = Flask(__name__)

# Helper function to convert Image to base64
def image_to_base64(image, format="PNG"):
    buffered = BytesIO()
    image.save(buffered, format=format)
    return base64.b64encode(buffered.getvalue()).decode('utf-8')

# Helper function to convert RGB to Hex
def rgb_to_hex(rgb):
    return '#{:02x}{:02x}{:02x}'.format(*rgb)

# Helper function to convert Hex to RGB
def hex_to_rgb(hex_code):
    hex_code = hex_code.lstrip('#')
    return tuple(int(hex_code[i:i+2], 16) for i in (0, 2, 4))

# Function to map detected colors to the nearest predefined hex codes
def match_to_closest_color(dominant_colors, predefined_colors):
    # Convert both dominant and predefined colors to RGB
    dominant_colors_rgb = [hex_to_rgb(c) for c in dominant_colors]
    predefined_colors_rgb = [hex_to_rgb(c) for c in predefined_colors]
    
    # Find the closest predefined color for each dominant color using Euclidean distance
    closest_colors_indices = pairwise_distances_argmin(dominant_colors_rgb, predefined_colors_rgb)
    
    # Return the matched predefined colors
    matched_colors = [predefined_colors[i] for i in closest_colors_indices]
    return matched_colors

# Function to find exact number of unique colors
def get_unique_colors(image, max_colors=10, predefined_hex_codes=None):
    image = image.convert('RGB')
    pixels = np.array(image).reshape(-1, 3)
    
    # Use KMeans to find the exact number of colors (max_colors)
    kmeans = KMeans(n_clusters=max_colors, random_state=0).fit(pixels)
    
    # Get the cluster centers (dominant colors)
    centers = kmeans.cluster_centers_
    
    # Convert RGB to hex
    dominant_colors = [rgb_to_hex(tuple(map(int, center))) for center in centers]
    
    # If predefined colors are provided, match the dominant colors to the nearest predefined ones
    if predefined_hex_codes:
        dominant_colors = match_to_closest_color(dominant_colors, predefined_hex_codes)
    
    # Remove duplicate colors and return only unique ones
    unique_colors = list(dict.fromkeys(dominant_colors))[:max_colors]  # Preserve order and limit to max_colors
    
    return unique_colors

@app.route('/get-unique-colors', methods=['POST'])
def get_unique_colors_route():
    if 'image' not in request.files:
        return jsonify({"error": "No image file provided"}), 400

    image_file = request.files['image']
    if not image_file:
        return jsonify({"error": "No image file provided"}), 400

    try:
        # Load the image
        image = Image.open(image_file)
        image = image.convert('RGB')  # Ensure image is in RGB mode

        # Predefined hex codes (ignoring black and white)
        predefined_hex_codes = ['#ff0000', '#00ff00', '#0000ff', '#ffff00', '#ff00ff', 
                                '#00ffff', '#808080', '#800080', '#008000', '#ff8000']

        # Convert hex codes to RGB tuples for comparison
        predefined_rgb_colors = [hex_to_rgb(color) for color in predefined_hex_codes]

        # Get image dimensions
        width, height = image.size

        # Extract unique colors from the image
        unique_colors_in_image = set()
        for x in range(width):
            for y in range(height):
                unique_colors_in_image.add(image.getpixel((x, y)))

        # Match predefined colors found in the image (in predefined order)
        matched_colors = []
        for color in predefined_rgb_colors:
            if color in unique_colors_in_image:
                matched_colors.append(rgb_to_hex(color))

        return jsonify({
            "unique_colors": matched_colors
        })

    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route('/replace-color', methods=['POST'])
def replace_color():
    if 'image' not in request.files:
        return jsonify({"error": "No image file provided"}), 400

    image_file = request.files['image']

    # Expecting a JSON object with target-replacement pairs
    color_map = request.form.get("color_map")
    if not color_map:
        return jsonify({"error": "Invalid input, no color map provided"}), 400

    try:
        # Parse the color map
        color_map = json.loads(color_map)

        # Convert hex codes to RGB tuples for all color pairs
        color_pairs = [(hex_to_rgb(target), hex_to_rgb(replacement)) for target, replacement in color_map.items()]

        # Load image from file
        image = Image.open(image_file)

        # Convert to RGB if not already in that mode
        image = image.convert("RGB")

        # Get image dimensions
        width, height = image.size

        # Tolerance for color replacement
        tolerance = 30  # Adjust this value for color matching precision

        # Iterate through each pixel and replace colors based on the color map
        for x in range(width):
            for y in range(height):
                current_color = image.getpixel((x, y))
                for target_color, replacement_color in color_pairs:
                    if np.linalg.norm(np.array(current_color) - np.array(target_color)) < tolerance:
                        image.putpixel((x, y), replacement_color)

        # Convert the modified image back to base64
        modified_image_base64 = image_to_base64(image, format="PNG")  # Specify the output format (e.g., PNG)

        return jsonify({"modified_image": modified_image_base64})
    
    except Exception as e:
        return jsonify({"error": str(e)}), 500


if __name__ == '__main__':
    app.run(debug=True)
