from fastapi import FastAPI, Depends, status, HTTPException
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from contextlib import asynccontextmanager
from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase
from pymongo.errors import ServerSelectionTimeoutError
import jwt
from jwt.exceptions import ExpiredSignatureError
from datetime import timedelta, datetime, timezone
import bcrypt
import os

import models, crud

# Environment variables
MONGO_URL=os.getenv('MONGO_URL')
JWT_ALGORITHM=os.getenv('JWT_ALGORITHM')
JWT_EXPIRE_MINUTES=int(os.getenv('JWT_EXPIRE_MINUTES'))
JWT_SECRET_KEY=os.getenv('JWT_SECRET_KEY')
MONGO_URL=os.getenv('MONGO_URL')
ADMIN_USER_USERNAME=os.getenv('ADMIN_USER_USERNAME')
ADMIN_USER_PASSWORD=os.getenv('ADMIN_USER_PASSWORD')

# Main application life cycle

async def create_admin_user(db: AsyncIOMotorDatabase):
    db_user = await crud.get_user(app.mongodb_db, ADMIN_USER_USERNAME)
    if not db_user:
        user_to_create = models.UserCreate(
            username=ADMIN_USER_USERNAME,
            plain_password=ADMIN_USER_PASSWORD,
            is_admin=True
        )
        await crud.create_user(app.mongodb_db, user_to_create)

@asynccontextmanager
async def db_lifespan(app: FastAPI):
    # start database connection
    app.mongodb_client = None
    try:
        app.mongodb_client = AsyncIOMotorClient(MONGO_URL)
        app.mongodb_db = app.mongodb_client.get_database("usersdb")
        await create_admin_user(app.mongodb_db)
        yield
    # close database connection
    finally:
        if app.mongodb_client:
            app.mongodb_client.close()

app = FastAPI(lifespan=db_lifespan)
            
# Authentication

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

def create_jwt_token(user_id: str, admin: bool):
    expire = datetime.now(timezone.utc) + timedelta(minutes=JWT_EXPIRE_MINUTES)
    payload_to_encode = {"sub": user_id, "exp": expire, "admin": admin}
    return jwt.encode(payload_to_encode, JWT_SECRET_KEY, algorithm=JWT_ALGORITHM)

async def get_current_user(token: str = Depends(oauth2_scheme), only_admin: bool = False):
    try:
        payload = jwt.decode(token, JWT_SECRET_KEY, algorithms=[JWT_ALGORITHM])
        user_id = payload.get("sub")
        is_admin = payload.get("admin")
    except ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token has been expired",
            headers={"WWW-Authenticate": "Bearer"},
        )
    except:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
    else:
        if only_admin and not is_admin:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Admin credentials required",
                headers={"WWW-Authenticate": "Bearer"},
            )
            
        return user_id

    
async def get_current_admin_user(token: str = Depends(oauth2_scheme)):
    return await get_current_user(token, only_admin=True)

@app.post("/token", response_model=models.Token)
async def get_access_token(login_data: OAuth2PasswordRequestForm = Depends()):
    user_login_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED, 
        detail="Wrong username or password",
        headers={"WWW-Authenticate": "Bearer"}
    )
    try:
        db_user = await crud.get_user(app.mongodb_db, login_data.username)
    except ServerSelectionTimeoutError:
        raise db_server_exception 
    except:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal Server Error (unable to verify user)"
        )        
    else:
        if not db_user:
            raise user_login_exception
        else:
            # Verify if login password matches password stored in database
            if bcrypt.checkpw(login_data.password.encode("utf-8"), db_user["hashed_password"]):
                jwt_encoded_token = create_jwt_token(str(db_user["_id"]), db_user["is_admin"])
                return models.Token(access_token=jwt_encoded_token, token_type="bearer")
            else:
                raise user_login_exception
            
# Requests

# Custom exception for database server errors
db_server_exception = HTTPException(
    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
    detail="Internal Server Error (unable to connect to database)"
)

@app.get(
    "/users", 
    response_model=list[models.User], 
    response_model_by_alias=False
)
async def get_all_users(current_admin_user_id: str = Depends(get_current_admin_user)):
    try:
        return await crud.get_all_users(app.mongodb_db)
    except ServerSelectionTimeoutError:
        raise db_server_exception     
    except:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal Server Error (unable to read users)"
        )

@app.post(
    "/users", 
    response_model=models.User, 
    response_model_by_alias=False,
    status_code=status.HTTP_201_CREATED,
    response_description="New user created"
)
async def create_user(user: models.UserCreate, current_admin_user_id: str = Depends(get_current_admin_user)):
    try:
        db_user = await crud.get_user(app.mongodb_db, user.username)
    except ServerSelectionTimeoutError:
        raise db_server_exception 
    except:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal Server Error (unable to verify username)"
        )        
    else:
        if db_user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, 
                detail="User with that name already exists"
            )
        try:
            return await crud.create_user(app.mongodb_db, user)
        except ServerSelectionTimeoutError:
            raise db_server_exception 
        except:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Internal Server Error (unable to create user)"
            )

@app.get("/test-auth")
async def test_auth(current_user_id: str = Depends(get_current_user)):
    return {"text": f"User with id {current_user_id} authenticated :)"}