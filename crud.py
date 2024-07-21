import bcrypt
from motor.motor_asyncio import AsyncIOMotorDatabase

import models

# Database operations

# Read
async def get_all_users(db: AsyncIOMotorDatabase):
    users = db.get_collection("users")
    return await users.find().to_list(None)

async def get_user(db: AsyncIOMotorDatabase, username: str):
    users = db.get_collection("users")
    return await users.find_one({ "username" : username })

# Create
async def create_user(db: AsyncIOMotorDatabase, user: models.UserCreate):
    users = db.get_collection("users")
    # hash password before storing it in database
    hashed_password = bcrypt.hashpw(user.plain_password.encode("utf-8"), bcrypt.gensalt())
    user_to_create = models.UserInDB(
        **user.model_dump(exclude=["id", "plain_password"]), 
        hashed_password=hashed_password
    )
    # create and find newly created user
    new_user = await users.insert_one(user_to_create.model_dump())
    created_user = await users.find_one({"_id" : new_user.inserted_id})
    return created_user