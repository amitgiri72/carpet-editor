from flask import Flask, request, jsonify
from io import BytesIO
from PIL import Image
import base64  # Import the base64 module

app = Flask(__name__)

# Helper function to convert Image to base64
def image_to_base64(image, format="PNG"):
    buffered = BytesIO()
    image.save(buffered, format=format)
    return base64.b64encode(buffered.getvalue()).decode('utf-8')

# Root URL
@app.route('/')
def home():
    return "<h1>Welcome to the Image Processing API</h1><p>Use the following endpoints:</p><ul><li>/get-unique-colors (POST)</li><li>/replace-color (POST)</li></ul>"

# API 1: Get unique colors in the image
@app.route('/get-unique-colors', methods=['POST'])
def get_unique_colors():
    if 'image' not in request.files:
        return jsonify({"error": "No image file provided"}), 400

    image_file = request.files['image']

    # Load image from file
    image = Image.open(image_file)

    # Convert to RGB if not already in that mode
    image = image.convert("RGB")

    # Get image dimensions
    width, height = image.size

    # Set to store unique colors
    unique_colors = set()

    # Process each pixel to find unique colors
    for x in range(width):
        for y in range(height):
            current_color = image.getpixel((x, y))
            unique_colors.add(current_color)

    # Convert the set to a list and sort it
    unique_colors = sorted(list(unique_colors))

    return jsonify({"unique_colors": unique_colors})

# API 2: Replace a target color with a replacement color
@app.route('/replace-color', methods=['POST'])
def replace_color():
    if 'image' not in request.files:
        return jsonify({"error": "No image file provided"}), 400

    image_file = request.files['image']
    target_color = request.form.getlist("target_color[]")
    replacement_color = request.form.getlist("replacement_color[]")

    if not target_color or not replacement_color:
        return jsonify({"error": "Invalid input"}), 400

    # Convert target_color and replacement_color to tuples
    target_color = tuple(map(int, target_color))
    replacement_color = tuple(map(int, replacement_color))

    # Load image from file
    image = Image.open(image_file)

    # Convert to RGB if not already in that mode
    image = image.convert("RGB")

    # Get image dimensions
    width, height = image.size

    # Replace the target color with the replacement color
    for x in range(width):
        for y in range(height):
            current_color = image.getpixel((x, y))
            if current_color == target_color:
                image.putpixel((x, y), replacement_color)

    # Convert the modified image back to base64
    modified_image_base64 = image_to_base64(image, format="PNG")  # Specify the output format (e.g., JPG)

    return jsonify({"modified_image": modified_image_base64})

if __name__ == '__main__':
    app.run(debug=True)