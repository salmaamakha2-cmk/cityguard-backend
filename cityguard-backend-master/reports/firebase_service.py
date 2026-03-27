import firebase_admin
from firebase_admin import credentials, messaging
import os

# Initialize Firebase (once)
def init_firebase():
    if not firebase_admin._apps:
        # For now we use mock mode - replace with real credentials later
        pass

def send_push_notification(fcm_token, title, body, data=None):
    """
    Send real push notification via Firebase FCM
    """
    try:
        init_firebase()
        
        message = messaging.Message(
            notification=messaging.Notification(
                title=title,
                body=body,
            ),
            data=data or {},
            token=fcm_token,
        )
        response = messaging.send(message)
        return {"success": True, "message_id": response}
        
    except Exception as e:
        # Mock fallback - log notification
        print(f"[FCM Mock] To: {fcm_token} | {title}: {body}")
        return {"success": False, "mock": True, "error": str(e)}


def send_notification_to_user(user, title, body, report_id=None):
    """
    Send push notification to a user if they have FCM token
    """
    data = {}
    if report_id:
        data['report_id'] = str(report_id)
    
    # Check if user has FCM token
    fcm_token = getattr(user, 'fcm_token', None)
    if fcm_token:
        return send_push_notification(fcm_token, title, body, data)
    else:
        print(f"[FCM] User {user.username} has no FCM token - notification saved to DB only")
        return {"success": False, "reason": "no_fcm_token"}