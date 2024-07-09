import speech_recognition as sr
import webbrowser
# webbrowser helps to search accross the web browser for the required data
import pyttsx3
# here pyttsx3 is python's text to speech module
import musicLibrary
import requests
import threading
import queue
# from gtts import gTTS
# import pygame
import os
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
import datetime
import re
import random
import difflib

SCOPES = ['https://www.googleapis.com/auth/calendar']

recognizer=sr.Recognizer()
# here Recognizer is a class which helps to take the speech recognization ability
engine=pyttsx3.init()
# here we initiated the ttsx engine
newsapikey = "539da9172744455298bb6c908e6d1652"
stop_listening=False
command_queue=queue.Queue()
weather_api_key="e51128f652e6706d782cbeab29e9564a"

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

def get_weather(city):
    url = f"http://api.openweathermap.org/data/2.5/weather?q={city}&appid={weather_api_key}&units=metric"
    try:
        r = requests.get(url)
        if r.status_code == 200:
            data = r.json()
            main = data['weather'][0]['main']
            description = data['weather'][0]['description']
            temp = data['main']['temp']
            weather_info = f"The current weather in {city} is {main} with {description}. The temperature is {temp} degrees Celsius."
            return weather_info
        else:
            print(f"Failed to get weather data. Status code: {r.status_code}, Response: {r.text}")
            return "Sorry, I couldn't fetch the weather information right now."
    except requests.exceptions.RequestException as e:
        print(f"Request failed: {e}")
        return "Sorry, I couldn't fetch the weather information right now."

def listen_for_city():
    r = sr.Recognizer()
    with sr.Microphone() as source:
        speak("Which city do you want to know the weather for?")
        audio = r.listen(source)
    try:
        city = r.recognize_google(audio)
        return city
    except sr.UnknownValueError:
        speak("Sorry, I didn't catch that. Please try again.")
        return None
    except sr.RequestError:
        speak("Sorry, I'm having trouble connecting to the speech service.")
        return None

def speak(text):
    engine.say(text)
    engine.runAndWait()

def processCommand(c):
    global stop_listening
    if "open google" in c.lower():
        webbrowser.open("https://google.com")
    elif "open linkedin" in c.lower():
        webbrowser.open("https://linkedin.com")
    elif "open facebook" in c.lower():
        webbrowser.open("https://facebook.com")
    elif "open youtube" in c.lower():
        webbrowser.open("https://youtube.com")
    elif "open lead code" in c.lower():
        webbrowser.open("https://leetcode.com/problemset/")
    elif "play" in c.lower():
        # Search for presence of "play" anywhere in the command
        potential_song_name = c.lower().split()[1:]  # Extract potential song name(s) after "play"

        # Iterate through music library to find any song name containing the search terms
        for song_name, link in musicLibrary.music.items():
            if any(term in song_name.lower() for term in potential_song_name):
                webbrowser.open(link)
                return  # Stop after finding a match

        print("Song not found in the library.")
    elif "news" in c.lower():
        r = requests.get("https://newsapi.org/v2/top-headlines?country=in&apiKey=539da9172744455298bb6c908e6d1652")
        if r.status_code == 200:
            data = r.json()
            articles = data.get('articles', [])
            
            def listen_for_stop():
                global stop_listening
                r = sr.Recognizer()
                with sr.Microphone() as source:
                    while not stop_listening:
                        try:
                            # print("Listening for 'stop' or 'pause' command...")
                            audio = r.listen(source, timeout=2)
                            word = r.recognize_google(audio)
                            print(f"Heard: {word}")
                            if "stop" in word.lower() or "pause" in word.lower():
                                command_queue.put("stop")
                                stop_listening = True
                        except sr.WaitTimeoutError:
                            continue
                        except sr.UnknownValueError:
                            continue
                        except sr.RequestError:
                            command_queue.put("error")
                            stop_listening = True

            stop_listening = False
            listener_thread = threading.Thread(target=listen_for_stop)
            listener_thread.start()
            
            for article in articles:
                if not command_queue.empty():
                    command = command_queue.get()
                    if command == "stop":
                        speak("Yes boss")
                        break
                    elif command == "error":
                        speak("Sorry, I'm having trouble connecting to the speech service.")
                        break

                speak(article['title'])
                print("Reading news:", article['title'])
                
            listener_thread.join()
        else:
            speak("Sorry boss, failed to seek headlines")
    
    elif "weather" in c.lower():
        city = listen_for_city()
        print(city)
        if city:
            weather_info = get_weather(city)
            speak(weather_info)
        else:
            speak("Sorry, I couldn't get the city name. Please try again.")

    elif "add event" in c.lower():
        speak("Sure, please provide the event Title.")
        event_details = listen_for_event_details()
        if event_details:
            print(event_details)
            speak("Please provide the date and time of the event")
            date_time = listen_for_event_details()
            date = parse_date_time_from_text(date_time)
            print(date)
            speak(f"Adding event on {date.strftime('%Y-%m-%d at %I:%M %p')}. Please provide a brief description of the event.")
            description = listen_for_event_details()
            print(description)
            if description:
                add_event_to_calendar(date, event_details, description)
        else:
            speak("Sorry, I couldn't get the event details. Please try again.")

    elif "delete event" in c.lower():
        speak("Sure, please provide the date and time of the event to delete.")
        event_details = listen_for_event_details()
        if event_details:
            date = parse_date_time_from_text(event_details)
            delete_event_from_calendar(date)
        else:
            speak("Sorry, I couldn't get the event details. Please try again.")


    elif "shut down" in c.lower() or "shutdown" in c.lower():
        finalCommand=["Sure boss, have a great day ahead !!","Yes boss, I'll take your leave","Farewell for now, remember to relax and unwind","Take care, looking forward for our new chat"]
        speak(finalCommand[random.randint(0,3)])
        exit(True)

    # elif:
        # let openAI handle the request
        # since openAI is paid to be used, this is not currently integrated
        # pass

    else:
        speak("Sorry, I didn't catch that command. Can you please repeat?")

if __name__=="__main__":
    speak("Initialising Jarvis...")
    while(True):
        # Listen for the wake word Jarvis
        # obtain audio from the microphone
        r = sr.Recognizer()
        

        # recognize speech using Google
        # Initially we went ahead with Sphinx but it gave errors so we use Google, although the options show google_cloud as option but google is also a function which works
        #  CMU Sphinx which is an open-source toolkit used for speech recognition, it also has a lightweight recognizer library called Pocketsphinx which will be used to recognize the speech.
        try:
            with sr.Microphone() as source:
                print("Listening for the wake word...")
                audio = r.listen(source,timeout=2,phrase_time_limit=1)
                # here with the timeout it will wait for a phrase to come only for 2 seconds and then give up with speech recognition error
                # phase time limit is the time it will listen to the phase and discontinue the further phrase and process the input which is taken till then
            word=r.recognize_google(audio)
            if word.lower()=="jarvis":
                speak("Yes")
                # Listen for command
                with sr.Microphone() as source:
                    print("Jarvis active...")
                    audio = r.listen(source)
                    command=r.recognize_google(audio)
                    # printing command for test
                    print(command)

                processCommand(command)
        except Exception as e:
            print("Error; {0}".format(e))