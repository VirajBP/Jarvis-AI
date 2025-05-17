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