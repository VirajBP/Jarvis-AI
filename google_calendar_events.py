from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
import re
import datetime
import os
import speech_recognition as sr
import pyttsx3
import pygame
from gtts import gTTS
import io

SCOPES = ['https://www.googleapis.com/auth/calendar']

def speak(text, lang='en'):
    if lang == 'en':
        # Use pyttsx3 for English
        engine = pyttsx3.init()
        engine.say(text)
        engine.runAndWait()
    else:
        # Use gTTS for non-English, but stream it
        tts = gTTS(text=text, lang=lang)
        fp = io.BytesIO()
        tts.write_to_fp(fp)
        fp.seek(0)

        pygame.mixer.init()
        pygame.mixer.music.load(fp)
        pygame.mixer.music.play()
        while pygame.mixer.music.get_busy():
            continue

def parse_date_time_from_text(event_details):
    date_pattern = r'(\d{1,2})\s*(?:st|nd|rd|th)?\s*(?:of)?\s*(January|February|March|April|May|June|July|August|September|October|November|December)?'
    time_pattern = r'(\d{1,2}:\d{2})\s*(AM|PM|a\.m\.|p\.m\.)?'

    date_match = re.search(date_pattern, event_details, re.IGNORECASE)
    time_match = re.search(time_pattern, event_details, re.IGNORECASE)

    if date_match:
        day = int(date_match.group(1))
        month_str = date_match.group(2)
        if month_str:
            month = datetime.datetime.strptime(month_str, '%B').month
        else:
            month = datetime.datetime.now().month  # Default to current month if not specified
    else:
        day = datetime.datetime.now().day
        month = datetime.datetime.now().month

    if time_match:
        time_str = time_match.group(1)
        period = time_match.group(2)
        if period:
            period = period.lower()  # Convert period to lowercase for consistent comparison
            hour, minute = map(int, time_str.split(':'))
            if period == "p.m." and hour < 12:
                hour += 12
            elif period == "a.m." and hour == 12:
                hour = 0
            time_str = f"{hour:02}:{minute:02}"
        time = datetime.datetime.strptime(time_str, '%H:%M').time()
    else:
        time = datetime.datetime.now().time()  # Default to current time if not specified

    event_date = datetime.datetime(datetime.datetime.now().year, month, day)
    event_time = datetime.datetime.combine(event_date, time)
    return event_time


def authorize_google_calendar():
    creds = None
    if os.path.exists('token.json'):
        creds = Credentials.from_authorized_user_file('token.json')
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                'credentials.json', SCOPES)
            creds = flow.run_local_server(port=0)
        with open('token.json', 'w') as token:
            token.write(creds.to_json())
    return creds


def add_event_to_calendar(date, summary, description):
    service = build('calendar', 'v3', credentials=authorize_google_calendar())
    event = {
        'summary': summary,
        'description': description,
        'start': {
            'dateTime': date.strftime('%Y-%m-%dT%H:%M:%S'),
            'timeZone': 'Asia/Kolkata',
        },
        'end': {
            'dateTime': (date + datetime.timedelta(hours=1)).strftime('%Y-%m-%dT%H:%M:%S'),
            'timeZone': 'Asia/Kolkata',
        },
    }
    try:
        event = service.events().insert(calendarId='primary', body=event).execute()
        speak(f"Event '{summary}' added to your calendar.")
    except Exception as e:
        speak(f"Failed to add event: {str(e)}")


def delete_event_from_calendar(date):
    service = build('calendar', 'v3', credentials=authorize_google_calendar())
    time_min = date.isoformat() + '+05:30'  # Adding IST offset

    events_result = service.events().list(calendarId='primary', timeMin=time_min, singleEvents=True, orderBy='startTime').execute()
    events = events_result.get('items', [])

    if not events:
        speak("No events found for that date.")
        return

    for event in events:
        start = event['start'].get('dateTime', event['start'].get('date'))
        if start.startswith(date.isoformat()):
            try:
                service.events().delete(calendarId='primary', eventId=event['id']).execute()
                speak(f"Event '{event['summary']}' deleted from your calendar.")
                return
            except Exception as e:
                speak(f"Failed to delete event: {str(e)}")
                return
    speak("No matching events found for that date and time.")


def listen_for_event_details():
    r = sr.Recognizer()
    with sr.Microphone() as source:
        print("Listening for event details...")
        audio = r.listen(source)
    try:
        event_details = r.recognize_google(audio)
        return event_details
    except sr.UnknownValueError:
        speak("Sorry, I didn't catch that. Please try again.")
        return None
    except sr.RequestError:
        speak("Sorry, I'm having trouble connecting to the speech service.")
        return None