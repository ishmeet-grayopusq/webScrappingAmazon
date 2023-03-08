import os
import json
import uvicorn
from jose import JWTError, jwt
from datetime import datetime, timedelta
from passlib.context import CryptContext  # For password hashing
from starlette.middleware.cors import CORSMiddleware
from fastapi import FastAPI, Response, Depends, HTTPException, status
from packages.models.models import UserData, UserInDB, TokenData, Token
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from packages.modules.product_data_handler import (
    process_all_urls,
    single_product_data_fetcher,
    process_historical_data,
)

SECRET_KEY = "82c878d39c89d6fdfe6ac87e26753c4393789ac9b344c1cb4a0ce3ccdc01d7b7"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30


pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth_2_scheme = OAuth2PasswordBearer(tokenUrl="token")


def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password):
    return pwd_context.hash(password)


def get_user(username: str):
    # TODO: Modify this to use MongoDB
    with open("Data/user_data.json", "r") as file_obj:
        user_data = file_obj.read()
    db = json.loads(user_data)
    if username in db:
        user_data = db[username]
        return UserInDB(**user_data)


def authenticate_user(username: str, password: str):
    user = get_user(username)
    if not user:
        return False
    if not verify_password(password, user.hashed_password):
        return False
    return user


def create_access_token(data: dict, expires_delta: timedelta or None = None):
    to_encode = data.copy()
    expire = (
        datetime.utcnow() + expires_delta if expires_delta else timedelta(minutes=15)
    )

    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt, expire


async def get_current_user(token: str = Depends(oauth_2_scheme)):
    credential_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if not username:
            return credential_exception

        token_data = TokenData(username=username)
    except JWTError:
        raise credential_exception

    user = get_user(username=token_data.username)
    if user is None:
        raise credential_exception
    return user


async def get_current_active_user(current_user: UserInDB = Depends(get_current_user)):
    if current_user.disabled:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Inactive user"
        )
    return current_user


app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_headers=["*"],
    allow_methods=["*"],
    allow_origins=["*"],
)


@app.get("/")
async def root():
    return {"app_status": "healthy"}


@app.post("/token", response_model=Token)
async def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends()):
    user = authenticate_user(form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token, expires_at = create_access_token(
        data={"sub": user.username}, expires_delta=access_token_expires
    )
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "expires_at": expires_at,
    }


@app.post("/register_user", dependencies=[Depends(get_current_active_user)])
async def register_user(user_data: UserData = Depends()):
    if get_user(user_data.user_name):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="User already exists in DB."
        )

    hashed_password = get_password_hash(user_data.password)
    with open("Data/user_data.json", "r") as file_obj:
        db_data = file_obj.read()
    db = json.loads(db_data)
    db[user_data.user_name] = {
        "username": user_data.user_name,
        "full_name": user_data.full_name,
        "email": user_data.email,
        "hashed_password": hashed_password,
        "disabled": False
    }

    with open("Data/user_data.json", "w") as file_obj:
        file_obj.write(json.dumps(db))

    return "User Registered"


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


@app.get(
    "/single_product/{product_name}", dependencies=[Depends(get_current_active_user)]
)
async def single_product_processor(product_name: str):
    """
    Extracts and returns info about 1 product from Amazon and Flipkart.
    """
    with open("Data/available_products.json", "r") as file_obj:
        product_data = json.loads(file_obj.read())
    if product_name not in product_data:
        return (
            "Product not tracked currently. Please execute '/product_info' endpoint to see list of supported "
            "product names. "
        )
    return await single_product_data_fetcher(product_name, product_data[product_name])


@app.get(
    "/historical_data/{product_name}", dependencies=[Depends(get_current_active_user)]
)
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
