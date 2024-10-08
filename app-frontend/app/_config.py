import os

ENV_VARS_REQUIRED = ["APP_BACKEND_PROTOCOL", "APP_BACKEND_HOST", "APP_BACKEND_PORT", "APP_BACKEND_ENDPOINT_COMPUTE_PREDICTIONS", "APP_BACKEND_ENDPOINT_FETCH_LAST_PREDICTIONS"]
APP_BACKEND_PROTOCOL = os.getenv("APP_BACKEND_PROTOCOL")
APP_BACKEND_HOST = os.getenv("APP_BACKEND_HOST")
APP_BACKEND_PORT = os.getenv("APP_BACKEND_PORT")
APP_BACKEND_ENDPOINT_COMPUTE_PREDICTIONS = os.getenv("APP_BACKEND_ENDPOINT_COMPUTE_PREDICTIONS")
APP_BACKEND_ENDPOINT_FETCH_LAST_PREDICTIONS = os.getenv("APP_BACKEND_ENDPOINT_FETCH_LAST_PREDICTIONS")

APP_BACKEND_API = f"{APP_BACKEND_PROTOCOL}://{APP_BACKEND_HOST}:{APP_BACKEND_PORT}"

for var in ENV_VARS_REQUIRED:
    if not os.getenv(var):
        raise ValueError(f"Missing environment variable: {var}")