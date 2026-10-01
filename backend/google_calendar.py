import os
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import Flow
from googleapiclient.discovery import build
from google.auth.transport.requests import Request




CLIENT_SECRET_FILE = os.path.join(os.path.dirname(__file__), 'client_secret.json')
TOKEN_FILE = os.path.join(os.path.dirname(__file__), 'token.json')
SCOPES = ['https://www.googleapis.com/auth/calendar']
REDIRECT_URI = "http://localhost:8000/api/calendar/callback"

def get_auth_url():
    flow = Flow.from_client_secrets_file(CLIENT_SECRET_FILE, scopes=SCOPES, redirect_uri=REDIRECT_URI)
    authorization_url, state = flow.authorization_url(access_type='offline', include_granted_scopes='true', prompt='consent')
    return authorization_url

def save_token(code):
    flow = Flow.from_client_secrets_file(CLIENT_SECRET_FILE, scopes=SCOPES, redirect_uri=REDIRECT_URI)
    flow.fetch_token(code=code)
    creds = flow.credentials
    with open(TOKEN_FILE, 'w') as token:
        token.write(creds.to_json())
    return creds

def get_service():
    if not os.path.exists(TOKEN_FILE):
        raise Exception("Not connected to Google Calendar yet.")
    
    creds = Credentials.from_authorized_user_file(TOKEN_FILE, SCOPES)
    if creds.expired and creds.refresh_token:
        creds.refresh(Request())
        with open(TOKEN_FILE, 'w') as token:
            token.write(creds.to_json())

    return build('calendar', 'v3', credentials=creds)

def create_event(project_name, client_name, deadline_str, project_id):
    service = get_service()
    event = {
        'summary': f'📅 Deadline: {project_name}',
        'description': f'Client: {client_name}\nProject ID: {project_id}',
        'start': {'date': deadline_str, 'timeZone': 'Asia/Kolkata'},
        'end': {'date': deadline_str, 'timeZone': 'Asia/Kolkata'},
        'reminders': {
            'useDefault': False,
            'overrides': [
                {'method': 'email', 'minutes': 10080},  # 1 week before
                {'method': 'popup', 'minutes': 4320},   # 3 days before
                {'method': 'popup', 'minutes': 2880},   # 2 days before
                {'method': 'popup', 'minutes': 1440},   # 1 day before
            ]
        }
    }
    event = service.events().insert(calendarId='primary', body=event).execute()
    return event['id']

def delete_event(google_event_id):
    if not google_event_id: return
    service = get_service()
    try:
        service.events().delete(calendarId='primary', eventId=google_event_id).execute()
    except Exception as e:
        print(f"Error deleting event: {e}")


def create_calendar_event(project_name: str, deadline_date: str, client_name: str = "") -> str:
    """Create an all-day event in Google Calendar for a project deadline."""
    try:
        if not os.path.exists(TOKEN_FILE):
            return "⚠️ Google Calendar is not connected. Please connect it in settings first."
        
        creds = Credentials.from_authorized_user_file(TOKEN_FILE)
        service = build('calendar', 'v3', credentials=creds)
        
        description = f"Project Deadline for {client_name}" if client_name else "Project Deadline"
        
        event = {
            'summary': f"🚨 Deadline: {project_name}",
            'description': description,
            'start': {
                'date': deadline_date, # Format: YYYY-MM-DD
                'timeZone': 'Asia/Kolkata', # Change to your timezone if needed
            },
            'end': {
                'date': deadline_date,
                'timeZone': 'Asia/Kolkata',
            },
        }
        
        created_event = service.events().insert(calendarId='primary', body=event).execute()
        return f"✅ Added '{project_name}' deadline to Google Calendar for {deadline_date}."
        
    except Exception as e:
        return f"❌ Error adding to Google Calendar: {str(e)}"