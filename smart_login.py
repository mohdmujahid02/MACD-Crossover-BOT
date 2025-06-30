# smart_login.py

from SmartApi.smartConnect import SmartConnect
import pyotp
import os
from dotenv import load_dotenv

load_dotenv()

def get_smartapi_client():
    try:
        api_key = os.getenv("SMARTAPI_KEY")
        client_id = os.getenv("SMARTAPI_CLIENT_ID")
        password = os.getenv("SMARTAPI_PASSWORD")
        totp_secret = os.getenv("TOTP")

        if not all([api_key, client_id, password, totp_secret]):
            raise ValueError("Missing SmartAPI environment variables.")

        client = SmartConnect(api_key=api_key)
        totp = pyotp.TOTP(totp_secret).now()

        auth_data = client.generateSession(client_id, password, totp)

        if not auth_data or "data" not in auth_data:
            raise ConnectionError("Login failed – check credentials or TOTP")

        print("✅ SmartAPI login successful")
        return client

    except Exception as e:
        print(f"❌ SmartAPI login failed: {e}")
        return None
