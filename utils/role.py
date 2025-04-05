import firebase_admin
from firebase_admin import credentials, firestore, initialize_app
from firebase_admin.auth import verify_id_token
import os

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if not firebase_admin._apps:
    cred = credentials.Certificate(os.path.join(BASE_DIR, "firebase-service-account.json"))
    initialize_app(cred)

db = firestore.client()

def get_user_info(username: str):
    users_ref = db.collection("users")
    query = users_ref.where("username", "==", username).limit(1).stream()

    for user in query:
        user_data = user.to_dict()
        return user_data.get("password", None), user_data.get("role", None)
    
    return None, None
