import os
from datetime import timedelta

class Config:
    # DEBUGGING: Fixed key to prevent rotation issues
    SECRET_KEY = os.getenv("SECRET_KEY", "fixed_debug_secret_key_12345")
    SQLALCHEMY_DATABASE_URI = os.getenv("DATABASE_URL", "sqlite:///t4alerts.db")
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # DEBUGGING: Fixed key and explicit location
    JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY", "fixed_debug_jwt_key_12345")
    JWT_TOKEN_LOCATION = ["headers"]
    JWT_HEADER_NAME = "Authorization"
    JWT_HEADER_TYPE = "Bearer"
    JWT_ACCESS_TOKEN_EXPIRES = timedelta(hours=1)
