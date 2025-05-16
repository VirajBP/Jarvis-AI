import speech_recognition as sr
import webbrowser
import pyttsx3
import musicLibrary
import requests
import threading
import queue
import os
import io
from googletrans import Translator
from textblob import TextBlob  # For Emotion Detection
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
import datetime
import re
import random
import difflib
from gtts import gTTS
import pygame
import wikipedia
import json
from forex_python.converter import CurrencyRates
from pint import UnitRegistry

# Initialize UnitRegistry for unit conversions
ureg = UnitRegistry()

# Initialize CurrencyRates for currency conversion
currency_rates = CurrencyRates()

# File to store todo list
TODO_FILE = 'todo_list.json'

SCOPES = ['https://www.googleapis.com/auth/calendar']

recognizer = sr.Recognizer()
engine = pyttsx3.init()
newsapikey = "539da9172744455298bb6c908e6d1652"
stop_listening = False
command_queue = queue.Queue()
weather_api_key = "e51128f652e6706d782cbeab29e9564a"
translator = Translator()  # Initialize translator

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



def detect_emotion(text):
    # Using TextBlob for simple sentiment analysis (emotion detection)
    blob = TextBlob(text)
    sentiment = blob.sentiment.polarity
    if sentiment > 0.1:
        return "happy"
    elif sentiment < -0.1:
        return "sad"
    else:
        return "neutral"

def get_language_code(language_name):
    # Dictionary mapping common language names to their codes
    language_codes = {
        # Indian languages
        'hindi': 'hi',
        'hindustani': 'hi',
        'indian': 'hi',
        'marathi': 'mr',
        'tamil': 'ta',
        'telugu': 'te',
        'bengali': 'bn',
        'gujarati': 'gu',
        'kannada': 'kn',
        'malayalam': 'ml',
        'punjabi': 'pa',
        'urdu': 'ur',
        
        # International languages
        'english': 'en',
        'spanish': 'es',
        'espanol': 'es',
        'french': 'fr',
        'francais': 'fr',
        'german': 'de',
        'deutsch': 'de',
        'chinese': 'zh-cn',
        'mandarin': 'zh-cn',
        'japanese': 'ja',
        'korean': 'ko',
        'russian': 'ru',
        'arabic': 'ar',
        'portuguese': 'pt',
        'italian': 'it',
        'dutch': 'nl',
        'greek': 'el',
        'turkish': 'tr',
        'vietnamese': 'vi',
        'thai': 'th',
        'indonesian': 'id'
    }
    return language_codes.get(language_name.lower(), 'en')

def translate_text(text, target_language):
    try:
        translator = Translator()
        translation = translator.translate(text, dest=target_language)
        print(f"\nOriginal text: {text}")
        print(f"Translated text ({target_language}): {translation.text}")
        return translation.text
    except Exception as e:
        print(f"Translation error: {str(e)}")
        return None

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

def listen_for_command(lang='en-in'):
    r = sr.Recognizer()
    with sr.Microphone() as source:
        print("Listening...")
        r.pause_threshold = 1
        audio = r.listen(source)
        try:
            print("Recognizing...")
            query = r.recognize_google(audio, language=lang)
            print(f"User said: {query}\n")
            return query
        except sr.UnknownValueError:
            speak("Sorry, I didn't catch that. Please try again.")
            return None
        except sr.RequestError:
            speak("Sorry, I'm having trouble connecting to the speech service.")
            return None

def parse_conversion_input(text):
    # Common patterns for conversion
    patterns = [
        r'convert\s+(\d+(?:\.\d+)?)\s+(\w+)\s+to\s+(\w+)',  # convert 5 kilometers to miles
        r'(\d+(?:\.\d+)?)\s+(\w+)\s+to\s+(\w+)',           # 5 kilometers to miles
        r'convert\s+(\d+(?:\.\d+)?)\s+(\w+)\s+in\s+(\w+)',  # convert 5 kilometers in miles
    ]
    
    for pattern in patterns:
        match = re.search(pattern, text.lower())
        if match:
            return float(match.group(1)), match.group(2), match.group(3)
    return None

def convert_currency(amount, from_currency, to_currency):
    try:
        # Clean up currency codes
        from_currency = from_currency.strip().upper()
        to_currency = to_currency.strip().upper()
        
        # Handle common currency names
        currency_mapping = {
            'dollar': 'USD',
            'dollars': 'USD',
            'euro': 'EUR',
            'euros': 'EUR',
            'pound': 'GBP',
            'pounds': 'GBP',
            'yen': 'JPY',
            'rupee': 'INR',
            'rupees': 'INR',
            'yuan': 'CNY',
            'franc': 'CHF',
            'francs': 'CHF',
            'australian dollar': 'AUD',
            'australian dollars': 'AUD',
            'canadian dollar': 'CAD',
            'canadian dollars': 'CAD'
        }
        
        from_currency = currency_mapping.get(from_currency.lower(), from_currency)
        to_currency = currency_mapping.get(to_currency.lower(), to_currency)
        
        result = currency_rates.convert(from_currency, to_currency, float(amount))
        return f"{amount} {from_currency} is equal to {result:.2f} {to_currency}"
    except Exception as e:
        return f"Sorry, I couldn't convert the currency. Error: {str(e)}"

def convert_units(value, from_unit, to_unit):
    try:
        # Clean up unit names
        from_unit = from_unit.strip().lower()
        to_unit = to_unit.strip().lower()
        
        # Handle common unit names and abbreviations
        unit_mapping = {
            # Length
            'kilometer': 'kilometer',
            'kilometers': 'kilometer',
            'km': 'kilometer',
            'meter': 'meter',
            'meters': 'meter',
            'm': 'meter',
            'centimeter': 'centimeter',
            'centimeters': 'centimeter',
            'cm': 'centimeter',
            'millimeter': 'millimeter',
            'millimeters': 'millimeter',
            'mm': 'millimeter',
            'mile': 'mile',
            'miles': 'mile',
            'mi': 'mile',
            'yard': 'yard',
            'yards': 'yard',
            'yd': 'yard',
            'foot': 'foot',
            'feet': 'foot',
            'ft': 'foot',
            'inch': 'inch',
            'inches': 'inch',
            'in': 'inch',
            
            # Weight
            'kilogram': 'kilogram',
            'kilograms': 'kilogram',
            'kg': 'kilogram',
            'gram': 'gram',
            'grams': 'gram',
            'g': 'gram',
            'pound': 'pound',
            'pounds': 'pound',
            'lb': 'pound',
            'ounce': 'ounce',
            'ounces': 'ounce',
            'oz': 'ounce',
            
            # Temperature
            'celsius': 'celsius',
            'c': 'celsius',
            'fahrenheit': 'fahrenheit',
            'f': 'fahrenheit',
            'kelvin': 'kelvin',
            'k': 'kelvin',
            
            # Volume
            'liter': 'liter',
            'liters': 'liter',
            'l': 'liter',
            'milliliter': 'milliliter',
            'milliliters': 'milliliter',
            'ml': 'milliliter',
            'gallon': 'gallon',
            'gallons': 'gallon',
            'gal': 'gallon',
            'quart': 'quart',
            'quarts': 'quart',
            'qt': 'quart',
            'pint': 'pint',
            'pints': 'pint',
            'pt': 'pint',
            'cup': 'cup',
            'cups': 'cup',
            'fluid ounce': 'fluid_ounce',
            'fluid ounces': 'fluid_ounce',
            'fl oz': 'fluid_ounce'
        }
        
        from_unit = unit_mapping.get(from_unit, from_unit)
        to_unit = unit_mapping.get(to_unit, to_unit)
        
        # Convert to pint Quantity
        quantity = float(value) * ureg(from_unit)
        # Convert to target unit
        result = quantity.to(to_unit)
        return f"{value} {from_unit} is equal to {result.magnitude:.2f} {to_unit}"
    except Exception as e:
        return f"Sorry, I couldn't convert the units. Error: {str(e)}"

def search_wikipedia(query):
    try:
        # Search Wikipedia
        search_results = wikipedia.search(query, results=3)
        if not search_results:
            return "Sorry, I couldn't find any information about that topic."
        
        # Get the summary of the first result
        summary = wikipedia.summary(search_results[0], sentences=2)
        return f"Here's what I found: {summary}"
    except Exception as e:
        return f"Sorry, I couldn't find information about that topic. Error: {str(e)}"

def load_todo_list():
    if os.path.exists(TODO_FILE):
        with open(TODO_FILE, 'r') as f:
            return json.load(f)
    return []

def save_todo_list(todo_list):
    with open(TODO_FILE, 'w') as f:
        json.dump(todo_list, f)

def add_todo_item(item):
    todo_list = load_todo_list()
    todo_list.append({
        'task': item,
        'completed': False,
        'created_at': datetime.datetime.now().isoformat()
    })
    save_todo_list(todo_list)
    return f"Added '{item}' to your todo list."

def list_todo_items():
    todo_list = load_todo_list()
    if not todo_list:
        return "Your todo list is empty."
    
    response = "Here's your todo list:\n"
    for i, item in enumerate(todo_list, 1):
        status = "✓" if item['completed'] else "□"
        response += f"{i}. [{status}] {item['task']}\n"
    return response

def complete_todo_item(index):
    todo_list = load_todo_list()
    try:
        index = int(index) - 1
        if 0 <= index < len(todo_list):
            todo_list[index]['completed'] = True
            save_todo_list(todo_list)
            return f"Marked '{todo_list[index]['task']}' as completed."
        return "Invalid todo item number."
    except ValueError:
        return "Please provide a valid number."

def delete_todo_item(index):
    todo_list = load_todo_list()
    try:
        index = int(index) - 1
        if 0 <= index < len(todo_list):
            deleted_item = todo_list.pop(index)
            save_todo_list(todo_list)
            return f"Deleted '{deleted_item['task']}' from your todo list."
        return "Invalid todo item number."
    except ValueError:
        return "Please provide a valid number."

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
    elif "convert" in c.lower():
        # Try to parse the conversion input
        conversion = parse_conversion_input(c)
        if conversion:
            value, from_unit, to_unit = conversion
            # Check if it's a currency conversion
            if any(currency in c.lower() for currency in ['dollar', 'euro', 'pound', 'yen', 'rupee', 'yuan', 'franc']):
                result = convert_currency(value, from_unit, to_unit)
            else:
                result = convert_units(value, from_unit, to_unit)
            speak(result)
        else:
            speak("I couldn't understand the conversion. Please try saying something like 'convert 5 kilometers to miles' or 'convert 100 dollars to euros'")
    
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
        r = requests.get("https://newsapi.org/v2/top-headlines?country=us&category=technology&apiKey=539da9172744455298bb6c908e6d1652")
        if r.status_code == 200:
            data = r.json()
            articles = data.get('articles', [])
            
            def listen_for_stop():
                global stop_listening
                r = sr.Recognizer()
                with sr.Microphone() as source:
                    while not stop_listening:
                        try:
                            audio = r.listen(source, timeout=2)
                            word = r.recognize_google(audio)
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
    
    elif "translate" in c.lower():
        speak("What is the language of the text you want to translate?")
        source_lang = listen_for_command()
        if source_lang:
            speak("What text would you like to translate?")
            text_to_translate = listen_for_command(get_language_code(source_lang))
            if text_to_translate:
                speak("To which language should I translate?")
                target_lang = listen_for_command()
                if target_lang:
                    source_code = get_language_code(source_lang)
                    target_code = get_language_code(target_lang)
                    
                    print(f"\nTranslating from {source_lang} ({source_code}) to {target_lang} ({target_code})")
                    translated_text = translate_text(text_to_translate, target_code)
                    
                    if translated_text:
                        print(f"\nTranslation complete!")
                        speak(f"Here's your translation:")
                        # First speak in original language
                        speak(text_to_translate, source_code)
                        print("\nSpeaking translation...")
                        # Then speak the translation
                        speak(translated_text, target_code)
                    else:
                        speak("Sorry, I couldn't translate that. Please try again.")
    elif "shut down" in c.lower() or "shutdown" in c.lower():
        finalCommand=["Sure boss, have a great day ahead !!","Yes boss, I'll take your leave","Farewell for now, remember to relax and unwind","Take care, looking forward for our new chat"]
        speak(finalCommand[random.randint(0,3)])
        exit(True)        
    else:
        speak("Sorry, I didn't catch that command. Can you please repeat?")

def emotional(emotion):
    if emotion=="neutral":
        pass
    elif emotion=="angry":
        speak("Boss, please calm down, its not good to be angry, tell me how can I assist you ?")
    elif emotion=="happy":
        speak("You feel delighted boss, its nice to see that, have a nice day ahead")
    elif emotion=="sad" or emotion=="nervous":
        speak("Boss dont be sad, tell me how can I assist you, maybe a joke would lighten you up !!")

if __name__ == "__main__":
    speak("Initialising Jarvis...")

    while True:
        try:
            with sr.Microphone() as source:
                print("Listening for the wake word...")
                audio = recognizer.listen(source, timeout=5, phrase_time_limit=1)
            word = recognizer.recognize_google(audio)
            if word.lower() == "jarvis":
                speak("Yes")
                with sr.Microphone() as source:
                    print("Jarvis active...")
                    audio = recognizer.listen(source)
                    command = recognizer.recognize_google(audio)
                    print(command)
                    flag=True
                    processCommand(command)
                    # Emotion Detection
                    if(flag):
                        emotion = detect_emotion(command)
                        speak(f"Also I sensed that you're feeling {emotion}.")
                        emotional(emotion)
                        flag=False

        except Exception as e:
            print("Error:", e)
