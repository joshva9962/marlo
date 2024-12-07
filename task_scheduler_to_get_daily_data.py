import requests
from pymongo import MongoClient
from datetime import datetime

# MongoDB Configuration
MONGO_URI = "mongodb://localhost:27017/"
DATABASE_NAME = "marlo"
COLLECTION_NAME = "api_data"

# API Configuration
API_URL = "https://12af-14-97-224-214.ngrok-free.app/index"  # Replace with the API URL you want to hit

# MongoDB Connection
client = MongoClient(MONGO_URI)
db = client[DATABASE_NAME]
collection = db[COLLECTION_NAME]

# Function to Fetch API Data and Save to MongoDB
def fetch_and_save_data():
    try:
        # Fetch data from API
        response = requests.get(API_URL)
        response.raise_for_status()  # Raise an exception for HTTP errors
        data = response.json()  # Assuming the API returns JSON data
        print('Fetched data:', data)
        
        # Check if the data is a list or a dictionary
        if isinstance(data, dict):
            # Add timestamp to the single dictionary
            data["fetched_at"] = datetime.now()
            # Insert single document into MongoDB
            collection.insert_one(data)
            print(f"Single document saved to MongoDB at {datetime.now()}")
        elif isinstance(data, list):
            # Add timestamp to each item in the list
            for item in data:
                if isinstance(item, dict):  # Ensure item is a dictionary
                    item["fetched_at"] = datetime.now()
            # Insert multiple documents into MongoDB
            collection.insert_many(data)
            print(f"{len(data)} documents saved to MongoDB at {datetime.now()}")
        else:
            print("Unexpected data format received from API.")
    except requests.exceptions.RequestException as e:
        print(f"Error fetching data from API: {e}")
    except Exception as e:
        print(f"Error saving data to MongoDB: {e}")

fetch_and_save_data()
