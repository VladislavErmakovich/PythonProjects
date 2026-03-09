from passlib.context import CryptContext
from datetime import datetime, timedelta
from jose import jwt

#import os
#from dotenv import load_dotenv

#load_dotenv()

# SECRET_KEY = os.getenv("SECRET_KEY")
# ALGORITHM = os.getenv("ALGORITHM", "HS256")
# ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", 30))

SECRET_KEY = "5e54e7eb8b4b0334899a4a15e476d41bfe4c1378e7ac7eb6ebcc812e97271c30" 
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60

password_context = CryptContext(schemes="bcrypt", deprecated="auto")

def get_password_hash(password):
    return password_context.hash(password)

def verify_password(hash_password, password):
    return password_context.verify(password, hash_password)

def create_access_token(data: dict):
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})

    encode_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encode_jwt