import requests
import json
import os
import datetime
from pint import UnitRegistry
import forex_python
EXCHANGE_RATES_API = "https://api.exchangerate-api.com/v4/latest/"

def convert_currency(amount, from_currency, to_currency):
    try:
        # Clean up currency codes
        from_currency = from_currency.strip().lower()
        to_currency = to_currency.strip().lower()
        
        # Handle common currency names
        currency_mapping = {
            'dollar': 'USD',
            'dollars': 'USD',
            'euro': 'EUR',
            'euros': 'EUR',
            'pound': 'GBP',
            'pounds': 'GBP',
            'yen': 'JPY',
            'yens': 'JPY',
            'rupee': 'INR',
            'rupees': 'INR',
            'yuan': 'CNY',
            'franc': 'CHF',
            'francs': 'CHF',
            'australian dollar': 'AUD',
            'australian dollars': 'AUD',
            'canadian dollar': 'CAD',
            'canadian dollars': 'CAD',
            'inr': 'INR',
            'usd': 'USD',
            'eur': 'EUR',
            'gbp': 'GBP',
            'jpy': 'JPY',
            'cny': 'CNY',
            'chf': 'CHF',
            'aud': 'AUD',
            'cad': 'CAD'
        }
        
        # Map the currencies to their codes
        from_code = currency_mapping.get(from_currency, from_currency.upper())
        to_code = currency_mapping.get(to_currency, to_currency.upper())
        
        print(f"Converting {amount} from {from_currency} ({from_code}) to {to_currency} ({to_code})")
        
        # Get exchange rates from the API
        response = requests.get(f"{EXCHANGE_RATES_API}{from_code}")
        if response.status_code == 200:
            data = response.json()
            if 'rates' in data and to_code in data['rates']:
                rate = data['rates'][to_code]
                result = float(amount) * rate
                return f"{amount} {from_currency} is equal to {result:.2f} {to_currency}"
            else:
                return f"Sorry, I couldn't find the exchange rate for {to_code}"
        else:
            return f"Sorry, I couldn't fetch the exchange rates. Error code: {response.status_code}"
    except Exception as e:
        print(f"Currency conversion error: {str(e)}")
        return f"Sorry, I couldn't convert the currency. Error: {str(e)}"