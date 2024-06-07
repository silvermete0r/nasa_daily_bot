import os
from dotenv import load_dotenv

load_dotenv()

TELEGRAM_API_KEY = os.getenv('TELEGRAM_API_KEY')
NASA_API_KEY = os.getenv('NASA_API_KEY')
WEATHER_API_KEY = os.getenv('WEATHER_API_KEY')