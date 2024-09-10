from flask import Flask, request, jsonify
from io import BytesIO
from PIL import Image
import base64

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

# Root URL
@app.route('/')
def home():
    return "<h1>Welcome to the Image Processing API</h1><p>Use the following endpoints:</p><ul><li>/get-unique-colors (POST)</li><li>/replace-color (POST)</li></ul>"

# API 1: Get unique colors in the image (returning hex codes)
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

    # Set to store unique colors (in hex format)
    unique_colors = set()

    # Process each pixel to find unique colors
    for x in range(width):
        for y in range(height):
            current_color = image.getpixel((x, y))
            hex_color = rgb_to_hex(current_color)  # Convert RGB to hex
            unique_colors.add(hex_color)

    # Convert the set to a sorted list
    unique_colors = sorted(list(unique_colors))

    return jsonify({"unique_colors": unique_colors})

# API 2: Replace a target color with a replacement color (using hex codes)
@app.route('/replace-color', methods=['POST'])
def replace_color():
    if 'image' not in request.files:
        return jsonify({"error": "No image file provided"}), 400

    image_file = request.files['image']
    target_hex = request.form.get("target_color")
    replacement_hex = request.form.get("replacement_color")

    if not target_hex or not replacement_hex:
        return jsonify({"error": "Invalid input"}), 400

    # Convert hex codes to RGB tuples
    target_color = hex_to_rgb(target_hex)
    replacement_color = hex_to_rgb(replacement_hex)

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
    modified_image_base64 = image_to_base64(image, format="PNG")  # Specify the output format (e.g., PNG)

    return jsonify({"modified_image": modified_image_base64})

if __name__ == '__main__':
    app.run(debug=True)
