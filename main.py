from fastapi import FastAPI, HTTPException, Depends, status
from pydantic import BaseModel
from motor.motor_asyncio import AsyncIOMotorClient
from bson import ObjectId
from typing import List, Dict
from datetime import datetime, timedelta
from fastapi.responses import JSONResponse


app = FastAPI()

# MongoDB client initialization
client = AsyncIOMotorClient("mongodb://localhost:27017")  # Replace with your MongoDB URI
db = client["marlo"]  # Replace with your database name
users_collection = db["users"]  # Replace with your collection name
apidata_collection = db['api_data']


# Pydantic model for user (with username and role)
class User(BaseModel):
    username: str
    role: str

# Helper function to convert MongoDB ObjectId to string
def user_helper(user) -> dict:
    return {
        "username": user["username"],
        "role": user["role"],
        "_id": str(user["_id"])
    }

@app.post("/users/")
async def create_user(user: User):
    # Check if the user already exists in MongoDB
    existing_user = await users_collection.find_one({"username": user.username})
    if existing_user:
        raise HTTPException(status_code=400, detail="Username already exists")
    
    # Insert the new user into MongoDB
    new_user = await users_collection.insert_one(user.dict())
    created_user = await users_collection.find_one({"_id": new_user.inserted_id})
    
    return {"msg": "User created successfully", "user": user_helper(created_user)}

@app.delete("/users/{username}")
async def delete_user(username: str):
    # Check if the user exists in MongoDB
    user = await users_collection.find_one({"username": username})
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Delete the user from MongoDB
    await users_collection.delete_one({"username": username})
    return {"msg": f"User {username} deleted successfully"}

# To run the app, use the command:
# uvicorn filename:app --reload

# Assuming User is a Pydantic model or a data class
class User(BaseModel):
    username: str
    role: str

# Assuming users_collection is a MongoDB collection instance
# User lookup function



def serialize_mongo_data(data: dict) -> dict:
    # Convert ObjectId to string for the _id field and handle other fields as needed
    if "_id" in data:
        data["_id"] = str(data["_id"])
    return data



async def get_current_user(username: str) -> User:
    user_data = await users_collection.find_one({"username": username})
    if not user_data:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    return User(**user_data)

# Dependency to check the user's role and return corresponding data
async def check_user_role(user: User = Depends(get_current_user)) -> List[str]:
    # Fetch the user's role from the database
    user_data = await users_collection.find_one({"username": user.username})
    
    if not user_data:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    role = user_data.get("role")

    # Check the role and return corresponding data
    if role == "admin":
        cursor = apidata_collection.find()
        data = [serialize_mongo_data(obj) for obj in await cursor.to_list(length=100)]  
        return {"message": "Success", "data": data}     # send All data
    elif role == "bulk":
        cursor = apidata_collection.find({"group": "bulk"})
        data = [serialize_mongo_data(obj) for obj in await cursor.to_list(length=100)]  
        return {"message": "Success", "data": data}  # Only bulk data
    elif role == "tanker":
        cursor = apidata_collection.find({"group": "tanker"})
        data = [serialize_mongo_data(obj) for obj in await cursor.to_list(length=100)]  
        return {"message": "Success", "data": data}  # Only tanker data
    else:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Unauthorized role")

@app.get("/user-data/")
async def get_user_data(user: User = Depends(get_current_user)):
    # Get the user role data
    data = await check_user_role(user)
    return {"message": "Success", "data": data}


def get_yesterday_date():
    return datetime.now() - timedelta(days=1)

# Function to calculate the percentage change in price
def calculate_percentage_change(today_price: float, yesterday_price: float) -> float:
    if yesterday_price == 0:
        return 0  # Avoid division by zero
    return ((today_price - yesterday_price) / yesterday_price) * 100

today_date = datetime.today().date()

# Aggregation
pipeline = [
    {
        '$sort': {
            'date': 1
        }
    }, {
        '$group': {
            '_id': {
                'group': '$group', 
                'id': '$id', 
                'date': '$date'
            }, 
            'values': {
                '$push': '$value'
            }
        }
    }, {
        '$sort': {
            '_id.date': 1
        }
    }, {
        '$group': {
            '_id': {
                'group': '$_id.group', 
                'id': '$_id.id'
            }, 
            'data': {
                '$push': {
                    'date': '$_id.date', 
                    'value': {
                        '$arrayElemAt': [
                            '$values', 0
                        ]
                    }
                }
            }
        }
    }, {
        '$project': {
            'group': '$_id.group', 
            'id': '$_id.id', 
            'data': {
                '$map': {
                    'input': '$data', 
                    'as': 'v', 
                    'in': {
                        'date': '$$v.date', 
                        'value': '$$v.value', 
                        'yesterday_value': {
                            '$let': {
                                'vars': {
                                    'prevDate': {
                                        '$dateToString': {
                                            'format': '%Y-%m-%d', 
                                            'date': {
                                                '$subtract': [
                                                    {
                                                        '$dateFromString': {
                                                            'dateString': '$$v.date'
                                                        }
                                                    }, 86400000
                                                ]
                                            }
                                        }
                                    }
                                }, 
                                'in': {
                                    '$arrayElemAt': [
                                        {
                                            '$filter': {
                                                'input': '$data', 
                                                'as': 'd', 
                                                'cond': {
                                                    '$eq': [
                                                        '$$d.date', '$$prevDate'
                                                    ]
                                                }
                                            }
                                        }, 0
                                    ]
                                }
                            }
                        }, 
                        'today_value': '$$v.value', 
                        'percentage_difference': {
                            '$cond': {
                                'if': {
                                    '$gt': [
                                        '$$v.value', 0
                                    ]
                                }, 
                                'then': {
                                    '$multiply': [
                                        {
                                            '$divide': [
                                                {
                                                    '$subtract': [
                                                        '$$v.value', {
                                                            '$ifNull': [
                                                                '$$v.yesterday_value.value', 0
                                                            ]
                                                        }
                                                    ]
                                                }, {
                                                    '$ifNull': [
                                                        '$$v.yesterday_value.value', 1
                                                    ]
                                                }
                                            ]
                                        }, 100
                                    ]
                                }, 
                                'else': 0
                            }
                        }
                    }
                }
            }
        }
    }
]

@app.get("/aggregated_data", response_model=List[Dict])
async def get_aggregated_data():
    # Execute aggregation pipeline and await the results
    results = await apidata_collection.aggregate(pipeline).to_list(None)  # Using to_list() to convert cursor to list

    # Return results as JSON response
    return JSONResponse(content=results)
