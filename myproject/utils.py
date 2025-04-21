# utils.py
import firebase_admin
from firebase_admin import auth
from rest_framework.exceptions import AuthenticationFailed

def verify_firebase_token(id_token):
    try:
        # Verify the Firebase ID token
        decoded_token = auth.verify_id_token(id_token)
        return decoded_token['uid']  # Firebase UID
    except Exception as e:
        raise AuthenticationFailed('Invalid or expired token')
