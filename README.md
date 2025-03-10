# Image classification for a refund department 
***

This project was created in order to improve the efficiency of clothing returns.  An online shopping platform 
for sustainable clothing is growing rapidly in terms of purchases, customers, and the unavoidable 
associated returns. This RESTful API was created to help relieve some of the work load of having to manually
categorize clothing orders for returns. 

## End Goal for Project

The intention for the design and creation of this application was to have it be completely integrated into
the cloud through Azure products.  This would provide improved scalability and data protection. 

## Design Goal 

The design goal:
- Create CNN (Convolutional Neural Network) clothing image classification model
    using TensorFlow tutorial and MNIST clothing dataset with KERAS
- Model to be stored remotely in Azure Blob Storage 
- Images to be batch processed every evening at 11pm stored remotely in Azure Blob Storage
- RESTful API developed using Flask, hosted on Azure Web App with Continuous Integration and 
    Continuous Deployment using GitHub Actions.
- Clothing categorization probabilities and most likely category classification stored remotely 
    using Azure SQL Server and Database

# Original Concept Architecture:
![ImageclassificationConcept (2).jpg](Images_ReadMe%2FImageclassificationConcept%20%282%29.jpg)

# SQL Database Entity-Relationship Diagram

![ClothingPredictionDatabase.drawio.png](Images_ReadMe%2FClothingPredictionDatabase.drawio.png)



## Challenges During Implementation
- Microsoft Entra ID Security Login for SQL Database
- System Requirements and Dependencies for Containerization 

Despite being able to use GitHub Actions to successfully build and deploy the Clothing Refund Flask App, 
the app is not yet working properly in Azure Web App.  I believe it is because I have not yet been able
to adjust for the system dependencies required to download the Tensorflow model from Azure Blob Storage, 
and perhaps there may be additional dependencies to run the ODBC Driver for SQL Server.

## Current Local Solution 

While Azure Web App is currently unable to automatically batch process images, solution is currently 
running on local computer using Microsoft Task Scheduler to send curl request to initiate run.

![Current_Image_ClassificationSolution (1).jpg](Images_ReadMe%2FCurrent_Image_ClassificationSolution%20%281%29.jpg)

## System Requirements 
***

- Python 3.12 +
- ODBC Driver 18 for SQL Server
- Microsoft Azure Portal Login

## Recreate Local Image Classification Solution
Note: Currently if all files were downloaded, access to Azure Blob Storage and Azure SQL Database 
is not accessible due to Firewall and Security Features. In order to recreate current solution, 
individual Azure Blob Storage and Azure SQL Database must be created. 

1. Create local project in VSCODE or preferred IDE 
2. Download model.ipynb and app.py
3. Create Virtual Environment using requirements.txt

``````commandline
pip install -r requirements.txt
``````

4. Run model.ipynb which will create a local file named: 'clothing_model.keras'

5. Log in to Microsoft Azure Portal 
6. Create a Resource Group which will contain all resources for the ClothingRefundFlaskApp
![img_4.png](Images_ReadMe/img_4.png)

7. Create an Azure Storage Account named: clothingimages
![img_5.png](Images_ReadMe/img_5.png)

8. Create two containers within Azure Storage Account: 
    - images (stores all in coming images to be processed.)
      (For Testing Purposes file named images/ClothingImages in GitHub Repository may be used)
    - model (stores TensorFlow model 'clothing_model.keras')
![img.png](Images_ReadMe/img.png)

9. Store files in corresponding containers.
![img_1.png](Images_ReadMe/img_1.png)
![img_2.png](Images_ReadMe/img_2.png)


10. In app.py update account_key variable (line 20)
   - account_key = 'xxxxxxx'
     - This information is found in Microsoft Azure Storage Account under Security + Networking tab: 
       - Access keys
       - Copy key1 and insert into account_key string variable
![img_3.png](Images_ReadMe/img_3.png)

11. Create Azure SQL Server and Database to store clothing category probabilities and image classification data.
    In Security: Make sure to select SQL Server Authentication only and save SQL UserId and SQL Password.
Server Name: datascience
Database Name: clothingrefund

![img.png](Images_ReadMe/img_6.png)

12. Using Query editor log in with SQL Server Authentication to create two tables to store image predictions 
and image probabilities. 
![img.png](Images_ReadMe/img_7.png)
    - Select New Query: 
        From SQL_Scripts folder run query: image_prediction 
        From SQL_Scripts folder run query: Image_Probabilities

13. Update SQL Database access information in app.py 
Note: Ideally SQL access would not be hardcoded. Originally Microsoft Entra ID was used, however this
required manually entering Azure Microsoft ID and Password for every run, limiting automatic deployment. 
![img.png](Images_ReadMe/img_9.png)


14. Set up Microsoft Task Scheduler creating a Basic Task to initiate batch processing 
    
Under Actions Tab:
- Select New 
- Name: Batch Processing
- Action: Start a Program
  - Settings: 
  - Program/Script: curl
    - Add arguments:
              ``````commandline
              curl -X POST "http://127.0.0.1:5000/prediction" -H "Content-Type: application/json"
              ``````
  - Triggers tab: 
    - Daily 
      - At 23:00 every day 
      - Satus: Enabled

15. Run Flask APP locally in python IDE
``````commandline
flask run
``````
Note: In order for Microsoft Task Scheduler to work correctly App must be running in IDE. 
For demonstration purposes time set to 15:42pm. 

![Screenshot 2025-03-04 154051.png](Images_ReadMe%2FScreenshot%202025-03-04%20154051.png)

![Screenshot 2025-03-04 154257.png](Images_ReadMe%2FScreenshot%202025-03-04%20154257.png)

Screen Shot of Image Prediction Table in Azure SQL Database 

![img_12.png](Images_ReadMe%2Fimg_12.png)

Screen Shot of Image Probabilities Table in Azure SQL Database

![img_13.png](Images_ReadMe%2Fimg_13.png)


## Ideal Solution Resolution

1. Finish Project by creating Azure Web App Service

2. Use GitHub Actions for Continuous Integration and Continuous Deployment with YAML file

![img_8.png](Images_ReadMe%2Fimg_8.png)

3. Use cron setting in YAML file and gunicorn start-up command to automatically run application at 11pm. 

![img_10.png](Images_ReadMe%2Fimg_10.png)

![img_11.png](Images_ReadMe%2Fimg_11.png)

   



