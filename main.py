import os
import json
import uvicorn
from fastapi import FastAPI, Request, Response, Depends, HTTPException, status
from pydantic import BaseModel
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from starlette.middleware.cors import CORSMiddleware
from product_data_handler import (
    process_all_urls,
    single_product_data_fetcher,
    process_historical_data,
)
from datetime import datetime, timedelta
from jose import JWTError, jwt
from passlib.context import CryptContext  # For password hashing

SECRET_KEY = "82c878d39c89d6fdfe6ac87e26753c4393789ac9b344c1cb4a0ce3ccdc01d7b7"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

db = {
    "admin": {
        "username": "admin",
        "full_name": "Admin",
        "email": "admin@grayopus.com",
        "hashed_password": "$2b$12$HoOKTkDS49.McMtjxF6/AOch7LCLzNkPmWBid6a5Ax6LrpAaoWZjW",
        "disabled": False,
    }
}


class Token(BaseModel):
    access_token: str
    token_type: str


class TokenData(BaseModel):
    username: str or None = None


class User(BaseModel):
    username: str
    email: str or None = None
    full_name: str or None = None
    disabled: bool or None = None


class UserInDB(User):
    hashed_password: str


pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth_2_scheme = OAuth2PasswordBearer(tokenUrl="token")


def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password):
    return pwd_context.hash(password)


def get_user(db, username: str):
    # TODO: Modify this to use MongoDB
    if username in db:
        user_data = db[username]
        return UserInDB(**user_data)


def authenticate_user(db, username: str, password: str):
    user = get_user(db, username)
    if not user:
        return False
    if not verify_password(password, user.hashed_password):
        return False

    return user


def create_access_token(data: dict, expires_delta: timedelta or None = None):
    to_encode = data.copy()
    expire = datetime.utcnow() + expires_delta if expires_delta else timedelta(minutes=15)

    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


async def get_current_user(token: str = Depends(oauth_2_scheme)):
    credential_exception = HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,
                                         detail="Could not validate credentials",
                                         headers={"WWW-Authenticate": "Bearer"})
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if not username:
            return credential_exception

        token_data = TokenData(username=username)
    except JWTError:
        raise credential_exception

    user = get_user(db, username=token_data.username)
    if user is None:
        raise credential_exception
    return user


async def get_current_active_user(current_user: UserInDB = Depends(get_current_user)):
    if current_user.disabled:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Inactive user")
    return current_user


app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_headers=["*"],
    allow_methods=["*"],
    allow_origins=["*"],
)


@app.post("/token", response_model=Token)
async def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends()):
    user = authenticate_user(db, form_data.username, form_data.password)
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,
                            detail="Incorrect username or password",
                            headers={"WWW-Authenticate": "Bearer"})
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(data={"sub": user.username}, expires_delta=access_token_expires)
    return {"access_token": access_token, "token_type": "bearer"}


@app.get("/")
async def root():
    return {"app_status": "healthy"}


@app.get("/product_info", dependencies=[Depends(get_current_active_user)])
async def product_info():
    """
    Returns a list of products that we can process as of now.
    """
    with open("Data/available_products.json", "r") as file_obj:
        product_data = file_obj.read()
    return json.loads(product_data)


@app.get("/all_products", dependencies=[Depends(get_current_active_user)])
async def all_url_processor():
    """
    Returns info about current prices of all products.
    """
    return await process_all_urls()


@app.get("/single_product/{product_name}", dependencies=[Depends(get_current_active_user)])
async def single_product_processor(product_name: str):
    """
    Extracts and returns info about 1 product from Amazon and Flipkart.
    """
    with open("Data/available_products.json", "r") as file_obj:
        product_data = json.loads(file_obj.read())
    if product_name not in product_data:
        return "Product not tracked currently. Please execute '/product_info' endpoint to see list of suppported product names."
    return await single_product_data_fetcher(product_name, product_data[product_name])


@app.get("/historical_data/{product_name}", dependencies=[Depends(get_current_active_user)])
async def historical_data_generator(product_name: str):
    """
    Generates historical data for 1 product from Amazon and Flipkart.
    """
    with open("Data/available_products.json", "r") as file_obj:
        product_data = json.loads(file_obj.read())
    return await process_historical_data(product_name, product_data[product_name])


if __name__ == "__main__":
    directories = os.listdir()
    if "Data" not in directories:
        os.mkdir("Data")
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
