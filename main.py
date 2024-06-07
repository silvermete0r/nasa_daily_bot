################################
# Project: NASA Daily Bot      #
# Author: Arman Zhalgasbayev   #
# © 2023 - All Rights Reserved #
################################

# Importing Dependencies
import requests
import threading
import telebot
import datetime as dt
import time
import csv
import json
from constants import TELEGRAM_API_KEY, NASA_API_KEY, WEATHER_API_KEY

# Initialize the Telegram bot
bot = telebot.TeleBot(TELEGRAM_API_KEY)

############################
# Bot Subscribers Settings #
############################


# Define a function to register a new subscriber
def register_subscriber(chat_id, first_name, last_name, username):
  with open('subscribers.csv', mode='a', newline='') as file:
    writer = csv.writer(file)
    writer.writerow([chat_id, first_name, last_name, username])


# Define a function to check if a subscriber is already registered
def is_subscriber_registered(chat_id):
  with open('subscribers.csv', mode='r') as file:
    reader = csv.reader(file)
    for row in reader:
      if row[0] == str(chat_id):
        return True
    return False


# Define a function to unregister a subscriber
def unregister_subscriber(chat_id):
  with open('subscribers.csv', mode='r') as file:
    reader = csv.reader(file)
    rows = [row for row in reader if row[0] != str(chat_id)]
  with open('subscribers.csv', mode='w', newline='') as file:
    writer = csv.writer(file)
    writer.writerows(rows)


###############################
# NASA API Functions Settings #
###############################


# Function for Getting the Astronomy Picture of the Day (APOD)
def get_apod(udate=None):
  if udate is None:
    url = f"https://api.nasa.gov/planetary/apod?api_key={NASA_API_KEY}"
  else:
    url = f"https://api.nasa.gov/planetary/apod?api_key={NASA_API_KEY}&date={udate}"
  response = requests.get(url)
  if response.status_code != 200:
    return None
  data = json.loads(response.text)
  if 'code' in data.keys():
    return None
  return data


# Convert Kelvin to Celsius and Fahrenheit function
def kelvin_to_celsius_fahrenheit(kelvin):
  celsius = round(kelvin - 273.1)
  fahrenheit = round(celsius * (9 / 5) + 32)
  return celsius, fahrenheit


# Function for Getting the information about astronauts in the ISS
def get_iss_astronauts():
  url = "http://api.open-notify.org/astros.json"
  response = requests.get(url)
  if response.status_code != 200:
    return None
  data = json.loads(response.text)
  return data


# Function for Getting current weather in Earth by City name
def get_city_weather(CITY):
  try:
    base_url = "http://api.openweathermap.org/data/2.5/weather?"
    url = base_url + "appid=" + WEATHER_API_KEY + "&q=" + CITY
    response = requests.get(url)
    if response.status_code != 200:
      return None
    response = json.loads(response.text)
    temp_kelvin = response['main']['temp']
    temp_celsius, temp_fahrenheit = kelvin_to_celsius_fahrenheit(temp_kelvin)
    feels_like_kelvin = response['main']['feels_like']
    feels_like_celsius, feels_like_fahrenheit = kelvin_to_celsius_fahrenheit(
      feels_like_kelvin)
    wind_speed = response['wind']['speed']
    humidity = response['main']['humidity']
    description = response['weather'][0]['description']
    sunrise_time = dt.datetime.utcfromtimestamp(response['sys']['sunrise'] +
                                                response['timezone'])
    sunset_time = dt.datetime.utcfromtimestamp(response['sys']['sunset'] +
                                               response['timezone'])
    data = f"<b>⛅ Information about weather in {CITY}:</b>\n\n<b>- Temperature in {CITY}:</b> {temp_celsius:.2f}°C or {temp_fahrenheit:.2f}°F \n<b>- Temperature in {CITY} feels like:</b> {feels_like_celsius:.2f}°C or {feels_like_fahrenheit:.2f}°F \n<b>- Humidity in {CITY}:</b> {humidity}% \n<b>- Wind Speed in {CITY}:</b> {wind_speed}m/s \n<b>- General Weather in {CITY}:</b> {description} \n<b>- Sun rises in {CITY} </b>at {sunrise_time} local time.\n<b>- Sun sets in {CITY} at {sunset_time} local time.</b>"
    return data
  except:
    return None


# Function for Getting the current ISS geolocation
def get_iss_geolocation():
  url = "http://api.open-notify.org/iss-now.json"
  response = requests.get(url)
  if response.status_code != 200:
    return None
  data = json.loads(response.text)
  return data


# Function for Getting Photo from NASA Mars exploration rovers: Curiosity, Opportunity, and Spirit
def get_mars_photo(rover, id):
  url = f"https://api.nasa.gov/mars-photos/api/v1/rovers/{rover}/photos?sol={id}&api_key={NASA_API_KEY}"
  response = requests.get(url)
  if response.status_code != 200:
    return None
  data = json.loads(response.text)
  return data['photos'][0]


# Function for Getting image from NASA Data Portal by keyword
def get_image_by_keyword(keyword):
  url = f"https://images-api.nasa.gov/search?q={keyword}"
  response = requests.get(url)
  if response.status_code != 200:
    return None
  data = json.loads(response.text)
  return data['collection']['items']


#########################
# Telegram Bot Settings #
#########################


# Daily APOD Notifications sending function
def send_daily_apod_message():
  try:
    data = get_apod()

    if data is None:
      return

    image_url = data['url']
    if 'copyright' in data.keys():
      author = data['copyright']
    else:
      author = "No Information"

    with open('subscribers.csv', mode='r') as file:
      reader = csv.reader(file)
      for row in reader:
        if row[0] == 'chat_id':
          continue
        chat_id = row[0]
        first_name = row[1]
        print(chat_id)
        msg_caption = f'''
🌄 Good morning, {first_name}! This is your daily reminder from NASA to have a productive day!

<b>✨ Title:</b> {data['title']}
<b>📅 Date:</b> {data['date']}
<b>👨‍🚀 Author:</b> {author}
<b>🌌 Explanation:</b> {data['explanation']}
'''

        try:
          bot.send_photo(chat_id,
                         image_url,
                         caption=f"<i>© Copyright: {author}</i>",
                         parse_mode='html')
          bot.send_message(chat_id, msg_caption, parse_mode='html')
        except Exception as e:
          print(f"Error sending message to chat_id: {chat_id}. {e}")
  except Exception as e:
    print(f"Error getting APOD data. {e}")


# Design 'Start' command
@bot.message_handler(commands=['start'])
def send_welcome(message):
  if not is_subscriber_registered(message.chat.id):
    register_subscriber(message.chat.id, message.chat.first_name,
                        message.chat.last_name, message.chat.username)
  bot.reply_to(message,
               f'''
👋 Dear, {message.chat.first_name}! Welcome to the NASA Daily Bot. I will help you with your Scientific Researches & give you a lot of interesting data from space in real-time!

📋 Main functions list:

🔰 <code>/apod YYYY-MM-DD</code> - Get Astronomy Picture of the Day (APOD) for date;
🔰 /apod - Just Get today's APOD;
🔰 /subscribe - Enable daily mailings - APODs;
🔰 /unsubscribe - Disable daily mailings - APODs;
🔰 /iss_geolocation - Tracking International Space Station (ISS) Geo-Location;
🔰 /iss_astronauts - Astronauts inside ISS;
🔰 /mars_weather - Weather in Mars;
🔰 <code>/earth_weather city </code> - Weather in Earth;
🔰 <code>/mars_photo rover_name 0-1000</code> - Picture from Mars Rover by id in range 0-1000 & <b>rover_name</b> can be <code>Curiosity</code>, <code>Opportunity</code> or <code>Spirit</code>;
🔰  <code>/image keyword</code> - Image/Video from NASA by Keyword;

📻 Houston, help: <code>supwithproject@gmail.com</code>
🚀 Explore: https://data.nasa.gov
''',
               disable_web_page_preview=True,
               parse_mode='html')


# Design 'APOD' sending command
@bot.message_handler(commands=['apod'])
def send_apod(message):
  msg_data = message.text.split()

  if len(msg_data) == 1:
    data = get_apod()
  elif len(msg_data) == 2:
    date_info = msg_data[1]
    data = get_apod(str(date_info))
  else:
    bot.reply_to(message, "Sorry, but you entered the command incorrectly!")
    return

  if data is None:
    bot.reply_to(message, "Sorry, but something went wrong!")
    return

  image_url = data['url']

  if 'copyright' in data.keys():
    author = data['copyright']
  else:
    author = "No Information"

  if 'title' in data.keys():
    title = data['title']
  else:
    title = "Unknown"

  msg_caption = f'''
<b>✨ Title:</b> {title}
<b>📅 Date:</b> {data['date']}
<b>👨‍🚀 Author:</b> {author}
<b>🌌 Explanation:</b> {data['explanation']}
  '''
  bot.send_photo(message.chat.id,
                 image_url,
                 caption=f"<i>© Copyright: {author}</i>",
                 parse_mode='html')
  bot.send_message(message.chat.id, msg_caption, parse_mode='html')


# Design 'Subscribe' command
@bot.message_handler(commands=['subscribe'])
def subsribe_apod(message):
  if is_subscriber_registered(message.chat.id):
    bot.reply_to(message, "You are already subscribed to APOD daily mailings!")
  else:
    register_subscriber(message.chat.id, message.chat.first_name,
                        message.chat.last_name, message.chat.username)
    bot.reply_to(
      message,
      "Well done, you are successfully subscribed to APOD daily mailings!")


# Design 'Image by keyword' command
@bot.message_handler(commands=['image'])
def send_image_by_keyword(message):
  try:
    text_data = message.text.split()
    if len(text_data) < 2:
      bot.reply_to(message, "Sorry, but something went wrong with command!")
      return
    data = get_image_by_keyword(message.text[7:])
    if data is None:
      bot.reply_to(message, "Sorry, but something went wrong!")
      return
    if len(data) == 0:
      bot.reply_to(
        message, f"Images by the keyword '{message.text[7:]}' just not found!")
      return
    data = data[0]['data'][0]
    img_url = f"https://images-assets.nasa.gov/image/{data['nasa_id']}/{data['nasa_id']}~thumb.jpg"
    key_words = ""
    for d in data['keywords']:
      key_words += f'#{d.replace(" ","_")}\t'
    msg_caption = f'''
<b>✨ Title:</b> {data['title']}
<b>📅 Date:</b> {data['date_created'][:11]}
<b>🔑 NASA ID:</b> <code>{data['nasa_id']}</code>
<i>{key_words}</i>
'''
    bot.send_photo(message.chat.id,
                   img_url,
                   caption=msg_caption,
                   parse_mode='html')
  except Exception as e:
    print(f"Error sending image by keyword. {e}")
    bot.reply_to(message, "Sorry, but something went wrong!")


# Design 'Unsubscribe' command
@bot.message_handler(commands=['unsubscribe'])
def unsubsribe_apod(message):
  if is_subscriber_registered(message.chat.id):
    unregister_subscriber(message.chat.id)
    bot.reply_to(
      message, "You are successfully unsubscribed from APOD daily mailings!")
  else:
    bot.reply_to(message, "You are not yet subscribed to APOD daily mailings!")


# Design 'Mars Rover Photo' command
@bot.message_handler(commands=['mars_photo'])
def send_mars_photo(message):
  try:
    text_data = message.text.split()
    if len(text_data) != 3:
      bot.reply_to(message, "Sorry, but something went wrong with command!")
      return
    if text_data[1].lower() not in ('curiosity', 'opportunity', 'spirit'):
      bot.reply_to(message, "Sorry, but something went wrong with rover name!")
      return
    if text_data[2].isnumeric():
      if int(text_data[2]) not in range(0, 1001):
        bot.reply_to(message, "Sorry, but something went wrong with id value!")
        return
    else:
      bot.reply_to(message, "Sorry, but something went wrong with id value!")
      return
    data = get_mars_photo(text_data[1], text_data[2])
    if data is None:
      bot.reply_to(message, "Sorry, but something went wrong!")
      return
    camera = f"{data['camera']['full_name']} ({data['camera']['name']})"
    earth_date = data['earth_date']
    landing_date = data['rover']['landing_date']
    launch_date = data['rover']['launch_date']
    mission_status = data['rover']['status']
    img_url = data['img_src']
    img_caption = f'''
📸 Camera: {camera}
- Rover: <i>{text_data[1]}</i>
- Sol: <i>{text_data[2]}</i>
- Earth date: <i>{earth_date}</i>
'''
    msg_content = f'''
📡 Information about rover:
- Rover name: <code>{text_data[1]}</code>
- Landing date: <code>{landing_date}</code>
- Launching date: <code>{launch_date}</code>
- Mission status: <code>{mission_status}</code>
'''
    bot.send_photo(message.chat.id,
                   img_url,
                   caption=img_caption,
                   parse_mode='html')
    bot.send_message(message.chat.id, msg_content, parse_mode='html')
  except Exception as e:
    bot.reply_to(message,
                 f"Sorry, but something went wrong! Error message: {str(e)}")


# Design 'Mars Weather' command
@bot.message_handler(commands=['mars_weather'])
def send_mars_weather(message):
  link_url = "https://mars.nasa.gov/layout/embed/image/insightweather/"
  msg_content = f"Check out [Mars Current Weather: {dt.date.today()}]({link_url})"
  bot.send_message(message.chat.id, msg_content, parse_mode='Markdown')


# Design 'Get Earth Weather' command
@bot.message_handler(commands=['earth_weather'])
def send_earth_weather(message):
  text_data = message.text.split()
  if len(text_data) < 2:
    bot.reply_to(message, "Sorry, but something went wrong with command!")
    return
  try:
    data = get_city_weather(message.text[15:])
    if data is None:
      bot.reply_to(message, f"Sorry, but no data about {message.text[15:]}!")
      return
    bot.send_message(message.chat.id, data, parse_mode='html')
  except Exception as e:
    bot.reply_to(message, f"Sorry, but something went wrong: {e}")


# Design 'ISS Geolocation' command
@bot.message_handler(commands=['iss_geolocation'])
def send_iss_geolocation(message):
  try:
    data = get_iss_geolocation()
    if data is None:
      bot.reply_to(message, "Sorry, but something went wrong!")
      return
    latitude = float(data['iss_position']['latitude'])
    longitude = float(data['iss_position']['longitude'])
    bot.send_location(message.chat.id,
                      latitude,
                      longitude,
                      horizontal_accuracy=1000,
                      heading=360)
  except Exception as e:
    bot.reply_to(message, f"Sorry, but something went wrong: {e}")


# Design 'ISS Astronauts' command
@bot.message_handler(commands=['iss_astronauts'])
def send_iss_astronauts(message):
  try:
    data = get_iss_astronauts()
    if data is None:
      bot.reply_to(message, "Sorry, but something went wrong!")
      return
    count = data['number']
    persons = data['people']
    astronauts_info = f"👨🏾‍🚀 At the moment, there are {count} astronauts in ISS:\n\n"
    for id, person in enumerate(persons):
      astronauts_info += f"{str(id+1)}) {person['name']} ({person['craft']})\n"

    bot.send_message(message.chat.id, astronauts_info, parse_mode='html')
  except Exception as e:
    bot.reply_to(message, f"Sorry, but something went wrong: {e}")


# Design 'Default Instructions' for handling any messages command
@bot.message_handler(func=lambda message: True)
def handle_any_messages(message):
  bot.send_message(message.chat.id,
                   f'''
📋 Main functions list:

🔰 <code>/apod YYYY-MM-DD</code> - Get Astronomy Picture of the Day (APOD) for date;
🔰 /apod - Just Get today's APOD;
🔰 /subscribe - Enable daily mailings - APODs;
🔰 /unsubscribe - Disable daily mailings - APODs;
🔰 /iss_geolocation - Tracking International Space Station (ISS) Geo-Location;
🔰 /iss_astronauts - Astronauts inside ISS;
🔰 /mars_weather - Weather in Mars;
🔰 <code>/earth_weather city </code> - Weather in Earth;
🔰 <code>/mars_photo rover_name 0-1000</code> - Picture from Mars Rover by id in range 0-1000 & <b>rover_name</b> can be <code>Curiosity</code>, <code>Opportunity</code> or <code>Spirit</code>;
🔰  <code>/image keyword</code> - Image/Video from NASA by Keyword;

📻 Houston, help: <code>supwithproject@gmail.com</code>
🚀 Explore: https://data.nasa.gov
''',
                   disable_web_page_preview=True,
                   parse_mode='html')


# Set the time for the daily notification (in 24-hour format)
notification_time = "01:00"

# Define the function that starts the bot polling in a separate thread
def start_polling():
  bot.polling()

# Start the bot polling in a separate thread
polling_thread = threading.Thread(target=start_polling)
polling_thread.start()

# Send Daily Notification
while True:
  now = dt.datetime.now().time().strftime('%H:%M')
  if now == notification_time:
    send_daily_apod_message()
    time.sleep(86400)
  else:
    time.sleep(1)