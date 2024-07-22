# FastAPI JWT authentication with MongoDB :closed_lock_with_key: :fallen_leaf:
## What is it :thinking:
This project demonstrates JWT-based authentication for FastAPI applications using MongoDB.
Users are created in the database and authenticated using JSON Web Tokens (JWTs).
Admin users have additional authorization to manage other users.

## Tech stack :hammer_and_wrench:
- Python :snake:
    - FastAPI 
    - PyJWT (to work with JWTs)
    - BCrypt (for secure password hashing)
    - motor (to asynchronously work with MongoDB)
- Docker, used to run the MongoDB server :whale:

## How to run it :man_technologist:
1. Create your .env file in the repository folder and add the following content (replace placeholders with actual values):

```bash
# JWT parameters
JWT_ALGORITHM=HS256
# For creating your secret key, you can run 'openssl rand -hex 32' in Git Bash
JWT_SECRET_KEY=<your secret key>
JWT_EXPIRE_MINUTES=30

# MongoDB client credentials
MONGO_INITDB_ROOT_USERNAME=<your mongo username>
MONGO_INITDB_ROOT_PASSWORD=<your mongo password>
MONGO_URL=mongodb://${MONGO_INITDB_ROOT_USERNAME}:${MONGO_INITDB_ROOT_PASSWORD}@mongo:27017/

# Default admin user credentials (created after first server run)
ADMIN_USER_USERNAME=<your default admin username>
ADMIN_USER_PASSWORD=<your default admin password>
```

2. Install Docker and verify your internet connectivity, as MongoDB and Python images will be downloaded :earth_americas:
3. Build the images and run the containers defined in the *docker-compose.yml* file: `docker-compose up`
4. Open: http://127.0.0.1:8000/docs
5. Verify authentication for all defined path operations and admin authorization for user management endpoints
