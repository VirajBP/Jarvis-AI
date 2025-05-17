import requests
from pint import UnitRegistry

ureg= UnitRegistry()
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