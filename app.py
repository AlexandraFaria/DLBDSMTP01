from flask import Flask, request, jsonify
import numpy as np
from PIL import Image
import tensorflow as tf
from datetime import datetime
from tensorflow.keras.models import load_model
from azure.storage.blob import BlobServiceClient
from io import BytesIO
import pyodbc
import os

"""Start APP"""

# Flask app
app = Flask(__name__)

# enter credentials for CNN model stored in Azure Storage Account Blob Container
account_name = "clothingimages"
# Azure Storage Account Access Key
account_key = "T0d5+k5UMpXhCQLvNE8PZJfRZ6gR1bWOconGDeOc3EbNOaHGGO4OGHVPtNZhOyMKi4Gil8ib2buj+AStlO8ygw=="
# Container Name that is holding CNN model
model_container_name = "model"
# Container name for images
image_container_name = "images"
# File name (blob)
model_name = "clothing_model.keras"

# Azure SQL Database Details for SQL Server Authentication
sql_server = "datascience.database.windows.net"
sql_database = "clothingrefund"
sql_driver = "ODBC Driver 18 for SQL Server"
sql_userid = "alexandrafaria"
sql_password = "#KkVNsR%p$06fEq"

"""Entra ID Authentication was not suitable for automatic deployment, as it needed in put each time prior to running."""
# Use Entra ID authentication
#sql_connect_str = f"DRIVER={sql_driver};SERVER={sql_server};DATABASE={sql_database};Authentication=ActiveDirectoryInteractive"

# SQL Server Authentication String
sql_connect_str = f"Driver={sql_driver};Server=tcp:{sql_server},1433;Database={sql_database};Uid={sql_userid};Pwd={sql_password};Encrypt=yes;TrustServerCertificate=no;Connection Timeout=30;"

# Use the client to connect to the container
blob_connect_str = ('DefaultEndpointsProtocol=https;AccountName=' + account_name + ';AccountKey=' + account_key +
                    ';EndpointSuffix=core.windows.net')
blob_service_client = BlobServiceClient.from_connection_string(blob_connect_str)


# load model from Azure Storage blob container
def download_model():
    blob_client = blob_service_client.get_blob_client(container=model_container_name, blob=model_name)

    # Download the blob (model file)
    model_data = blob_client.download_blob().readall()

    # Save model locally with given file name.
    model_path = "test_model.keras"

    # Opens model in write-binary and creates new file.
    with open(model_path, "wb") as f:
        f.write(model_data)
    # Load model using tensorflow.
    return load_model(model_path)


# Load model once when app starts
model = download_model()


# Create connection with sql database using connection string
def connect_db():
    try:
        conn = pyodbc.connect(sql_connect_str)
        print("Connection successful!")
        return conn
    except Exception as e:
        print(f"Connection failed: {e}")
        return None


# Function to download an image from Azure Storage image container
def download_image(image_name):
    try:
        # Establish connection with blob container
        blob_client = blob_service_client.get_blob_client(container=image_container_name, blob=image_name)
        if not blob_client.exists():
            return None
        # reads all data in blob and returns as bytes.
        image_data = blob_client.download_blob().readall()
        # Opens Image in bytes and converts to grey scale.
        image = Image.open(BytesIO(image_data)).convert("L")  # Convert to grayscale (if needed)
        return image
    except Exception as e:
        # Error for failed image download.
        print(f"Image download failed: {e}")
        return None


# Category Names to be used to convert numeric label to string.
category_names = ["T-shirt/top", "Trouser", "Pullover", "Dress", "Coat",
                  "Sandal", "Shirt", "Sneaker", "Bag", "Ankle boot"]


# Create method to preprocess images prior to sending to model
def preprocess_image(image):
    """Resize, normalize, and reshape image
    to be the same size MNIST dataset"""
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


def save_prediction_to_db(image_name, predicted_category, probabilities):
    # Create connection to SQL database
    conn = connect_db()

    # Send error message if no connection.
    if conn is None:
        return False

    try:
        cursor = conn.cursor()
        # Insert into image_prediction table
        timestamp = datetime.now()
        insert_image_prediction_query = """
        INSERT INTO image_prediction (image_filename, predicted_category, timestamp)
        OUTPUT INSERTED.image_id
        VALUES(?, ?, ?);
        """

        # Get primary key from image_prediction table
        cursor.execute(insert_image_prediction_query, (image_name, predicted_category, timestamp))
        image_id = cursor.fetchone()[0]  # Get inserted image_id

        # Convert numpy array to flattened list of probabilities in float form with 4 decimals
        probabilities = [round(float(prob), 4) for prob in probabilities.flatten().tolist()]

        # Insert probabilities into coordinated clothing categories.
        insert_probabilities_query = """
        INSERT INTO image_probabilities (image_id, t_shirt, trouser, pullover, dress, coat, sandal, shirt, sneaker, bag, ankle_boot)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """
        cursor.execute(insert_probabilities_query, (image_id, *probabilities))

        # Commit all entries, close cursor, and close the connection.
        conn.commit()
        cursor.close()
        conn.close()
        print(f" Prediction saved: {image_name} = {predicted_category}")
        return True

    except Exception as e:
        print(f" Database insert failed: {e}")
        return False


@app.route("/prediction", methods=["POST"])
def prediction():
    #Create a list of all blobs in container
    blob_list = blob_service_client.get_container_client(image_container_name).list_blobs()
    # from list of blobs, create list of blob names.
    image_names = [blob.name for blob in blob_list]

    # For Postman responses. Store results.
    results = []

    for image_name in image_names:
        image = download_image(image_name)
        if image is None:
            results.append({"image_name": image_name, "error": "Image not found"})
            continue

        # Process Image using preprocess_image function
        processed_image = preprocess_image(image)
        # Use CNN model to create predictions.  Returns in logits format.
        logits = model.predict(processed_image)
        # Convert logits to probabilities using softmax layer.
        probabilities = tf.nn.softmax(logits).numpy()
        # Category with maximum probability is the clothing category classification in numeric format.
        highest_prediction = np.argmax(probabilities)
        # Convert clothing category numeric format to string.
        predicted_category = category_names[highest_prediction]

        # Save maximum category prediction and clothing category probabilities to Azure SQL database.
        save_status = save_prediction_to_db(image_name, predicted_category, probabilities)
        if not save_status:
            results.append({"image_name": image_name, "error": "Failed to save prediction"})
        else:
            results.append({"image_name": image_name, "predicted_category": predicted_category})

    return jsonify({"batch_results": results})


if __name__ == '__main__':
    port = int(os.environ.get("PORT", 8000))  # Default to 8000
    app.run(host='0.0.0.0', port=port)