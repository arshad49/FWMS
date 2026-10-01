from google_calendar import get_service

try:
    print("Trying to connect to Google Calendar...")
    service = get_service()
    print("✅ SUCCESS! Connected to Google Calendar.")
    
    # Try to fetch your next 3 events
    events_result = service.events().list(calendarId='primary', maxResults=3, singleEvents=True, orderBy='startTime').execute()
    events = events_result.get('items', [])
    
    if not events:
        print("No upcoming events found (which is fine!).")
    else:
        print(f"Found {len(events)} events in your calendar:")
        for event in events:
            print(f" - {event.get('summary')}")
            
except Exception as e:
    print(f"❌ FAILED! Error: {e}")