from flask import Flask, request, jsonify
import numpy as np
from PIL import Image
import io
import keras

app = Flask(__name__)


# Create method to preprocess images prior to sending to model
def preprocess_image(image):
    """Convert image to grayscale, resize, normalize, and reshape
    to be the same size MNIST dataset"""
    # Convert to grayscale
    image = image.convert("L")
    # Resize to match model dimensions
    image = image.resize((28, 28))
    # Normalize pixel values (all greyscale values are between 0 and 255)
    image = np.array(image) / 255.0
    # Invert pixel values (MNIST dataset is inverted on black background)
    image = 1 - image
    # Add batch dimension (number within a batch)
    image = np.expand_dims(image, axis=0)
    # Add greyscale channel dimension for CNN as the last dimension
    image = np.expand_dims(image, axis=-1)
    # numpy array [ batch #, height, width, channel]
    return image


@app.route("/prediction", methods=["POST"])
def prediction():

    if "file" not in request.files:
        return jsonify({"error": "No file uploaded"}), 400

    # Designates sent file from Postman request.
    file = request.files["file"]
    # Open image from the uploaded file
    image = Image.open(io.BytesIO(file.read()))
    # Preprocess the image using the function created above
    image = preprocess_image(image)
    # Load model
    clothing_model = keras.models.load_model('clothing_model.keras')
    # Make prediction
    predictions = clothing_model.predict(image)
    highest_prediction = np.argmax(predictions).tolist()

    return jsonify({
        "message": "Prediction sent.",
        "image_category prediction": highest_prediction
    })


if __name__ == "main":
    app.run()
