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
import datetime
import random
from gtts import gTTS
import pygame
import wikipedia
from pint import UnitRegistry
from get_language_code import get_language_code, translate_text
from convert_currency import convert_currency
from convert_units import convert_units
from todo_tasks import load_todo_list, save_todo_list, add_todo_item, list_todo_items, complete_todo_item, delete_todo_item
from google_calendar_events import add_event_to_calendar, delete_event_from_calendar, listen_for_event_details, parse_date_time_from_text
from city_weather import get_weather, listen_for_city
from parseForUnitConversion import parse_conversion_input

recognizer = sr.Recognizer()
engine = pyttsx3.init()
newsapikey = "539da9172744455298bb6c908e6d1652"
stop_listening = False
command_queue = queue.Queue()

translator = Translator()  # Initialize translator

def set_windows_reminder(reminder_text, reminder_time):
    run_time = reminder_time.strftime("%H:%M")
    task_name = f"JarvisVoiceReminder_{datetime.datetime.now().strftime('%Y%m%d%H%M%S')}_{random.randint(1000,9999)}"

    script_dir = os.path.expanduser("~\\JarvisReminders")
    os.makedirs(script_dir, exist_ok=True)
    py_path = os.path.join(script_dir, f"{task_name}.py")

    with open(py_path, "w") as py_file:
        py_file.write(f'''import pyttsx3, os
engine = pyttsx3.init()
engine.say("{reminder_text}")
engine.runAndWait()
os.remove(__file__)
''')

    command = (
        f'schtasks /Create /SC ONCE /TN "{task_name}" '
        f'/TR "python \\"{py_path}\\"" '
        f'/ST {run_time} /F'
    )

    os.system(command)
    speak(f"Voice reminder set: '{reminder_text}' at {run_time}")


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
            currency_indicators = [
                'dollar', 'dollars', 'euro', 'euros', 'pound', 'pounds',
                'yen', 'yens', 'rupee', 'rupees', 'yuan', 'franc', 'francs',
                'australian dollar', 'canadian dollar', 'australian dollars',
                'canadian dollars', 'inr', 'usd', 'eur', 'gbp', 'jpy', 'cny',
                'chf', 'aud', 'cad'
            ]
            if any(indicator in c.lower() for indicator in currency_indicators):
                result = convert_currency(value, from_unit, to_unit)
            else:
                result = convert_units(value, from_unit, to_unit)
            speak(result)
        else:
            speak("I couldn't understand the conversion. Please try saying something like 'convert 5 kilometers to miles' or 'convert 100 dollars to euros'")
    
    elif "search wikipedia" in c.lower() or "tell me about" in c.lower():
        # Extract the search query from the command
        query = c.lower().replace("search wikipedia", "").replace("tell me about", "").strip()
        if query:
            result = search_wikipedia(query)
            speak(result)
        else:
            speak("What would you like to know about?")
            query = listen_for_command()
            if query:
                result = search_wikipedia(query)
                speak(result)
    
    elif "add to do" in c.lower():
        # Extract the todo item from the command
        todo_item = c.lower().replace("add to do", "").strip()
        if todo_item:
            result = add_todo_item(todo_item)
            speak(result)
        else:
            speak("What would you like to add to your todo list?")
            item = listen_for_command()
            if item:
                result = add_todo_item(item)
                speak(result)
    
    elif "list to dos" in c.lower() or "show to dos" in c.lower():
        result = list_todo_items()
        speak(result)
    
    elif "complete to do" in c.lower():
        # Extract the todo number from the command
        try:
            number = int(''.join(filter(str.isdigit, c)))
            result = complete_todo_item(number)
            speak(result)
        except ValueError:
            speak("Which todo item would you like to mark as completed? Please say the number.")
            index = listen_for_command()
            if index:
                result = complete_todo_item(index)
                speak(result)
    
    elif "delete to do" in c.lower():
        # Extract the todo number from the command
        try:
            number = int(''.join(filter(str.isdigit, c)))
            result = delete_todo_item(number)
            speak(result)
        except ValueError:
            speak("Which todo item would you like to delete? Please say the number.")
            index = listen_for_command()
            if index:
                result = delete_todo_item(index)
                speak(result)
    
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
    elif "remind me" in c.lower() or "set a reminder" in c.lower() or "set reminder" in c.lower() or "set an alarm" in c.lower() or "set an alarm for" in c.lower():
        speak("Sure, please tell me the reminder text.")
        reminder_text = listen_for_command()
        if reminder_text:
            speak("Please tell me the date and time for the reminder.")
            date_time = listen_for_event_details()
            if date_time:
                date = parse_date_time_from_text(date_time)
                set_windows_reminder(reminder_text, date)
            else:
                speak("Sorry, I couldn't get the date and time. Please try again.")
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

    
    try:
        with sr.Microphone() as source:
            print("Listening for the wake word...")
            audio = recognizer.listen(source, timeout=5, phrase_time_limit=1)
        word = recognizer.recognize_google(audio)
        if word.lower() == "jarvis":
            speak("Yes")
            while True:
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
                        if(emotion=="sad" or emotion=="angry" or emotion=="nervous"):
                            # Speak the detected emotion
                            # print(f"Detected Emotion: {emotion}")
                            # if emotion != "neutral":
                            speak(f"Also I sensed that you're feeling {emotion}.")
                            emotional(emotion)
                        flag=False

    except Exception as e:
        print("Error:", e)
