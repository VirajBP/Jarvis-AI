import requests
import speech_recognition as sr
import pyttsx3
import io
import pygame
import os
from gtts import gTTS
from dotenv import weather_api_key


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