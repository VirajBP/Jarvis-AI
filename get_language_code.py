from googletrans import Translator

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
