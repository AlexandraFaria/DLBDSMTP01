from flask import Flask, request, jsonify
import numpy as np
from PIL import Image
import io
import keras
import tensorflow as tf

app = Flask(__name__)

# Category Names to be used to convert numeric label to string.
category_names = ["T-shirt/top", "Trouser", "Pullover", "Dress", "Coat",
                  "Sandal", "Shirt", "Sneaker", "Bag", "Ankle boot"]


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
    # Make predictions (returns in the form of logits)
    logits = clothing_model.predict(image)

    # Apply softmax layer to convert logits to probabilities that sum to 1,
    # and normalize the output
    probabilities = tf.nn.softmax(logits).numpy()

    # Predicted numeric class
    highest_prediction_number = np.argmax(probabilities)

    # Predicted numeric class transformed to category name
    highest_prediction_name = category_names[highest_prediction_number]

    # Create a dictionary to return the category names with associated probabilities
    category_probabilities = {category_names[i]: round(float(probabilities[0, i]), 4) for i in
                              range(len(category_names))}

    return jsonify({
        "Predicted Class:": highest_prediction_name,
        "List of Class probabilities": category_probabilities
    })


if __name__ == "main":
    app.run()
