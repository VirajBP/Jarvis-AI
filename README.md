🎙️ Jarvis – Your Voice-Controlled AI Assistant 🤖
Jarvis is a voice-activated personal assistant built in Python, designed to handle everyday tasks via simple natural voice commands. It combines speech recognition, text-to-speech, external API integrations, and Windows automation tools to provide a seamless, hands-free digital assistant experience.

🚀 Features
🗣️ Voice Interaction
Speech Recognition: Uses speech_recognition to convert voice commands to text.

Speech Output: Responds using pyttsx3, enabling full offline voice feedback.

🔔 Intelligent Reminders (Windows Task Scheduler)
Set reminders using natural voice, e.g., "Remind me to drink water at 5:00 PM."

Uses Windows Task Scheduler to trigger pop-up + audio reminders at the specified time.

Self-deleting VBScript ensures no residual files after the reminder is executed.

🎵 Play Music via YouTube
Recognizes commands like "Play [song name]" and opens corresponding YouTube videos in the browser.

Uses pywhatkit.playonyt() for accurate music searches and playback.

📅 Google Calendar Integration
Adds and deletes events to/from Google Calendar.

Parses natural language input like "Add dentist appointment tomorrow at 3 PM." using NLP.

Requires a one-time user authentication with Google (OAuth 2.0 token flow).

🌤️ Real-Time Weather Information
Provides live weather reports using the OpenWeatherMap API.

Example: "What's the weather in Chennai?"

📰 News Updates
Fetches latest headlines using the NewsAPI.

Responds to commands like "Tell me the latest news." or "Any tech news?"

😄 Emotion Detection
Analyzes emotional tone of your statements using TextBlob.

Adapts responses based on positive, neutral, or negative sentiment.

🌍 Language Translation
Translates between major languages using googletrans.

Example: "Translate 'good morning' to French." ➝ "Bonjour"

📦 Technologies Used
Feature	                              Library / Tool
Voice Recognition	                speech_recognition
Voice Output	                 pyttsx3, gTTS (optional)
Music (YouTube)	                        pywhatkit
Google Calendar	            google-api-python-client, oauth2client
Weather Updates	                requests, OpenWeatherMap API
News Fetching	                    requests, NewsAPI
Emotion Detection	                     textblob
Language Translation	               googletrans
Reminders	               os, datetime, Task Scheduler (via os.system)

⚙️ Requirements
Python 3.7+

Internet connection for online features

Windows OS (for reminder system using Task Scheduler)

