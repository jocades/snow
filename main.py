import os
import time
import json
import smtplib
import requests
import schedule
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from pydantic import BaseModel
from dotenv import load_dotenv


load_dotenv('.env.local')

API_KEY = os.getenv('WEATHER_API_KEY')
EMAIL = os.getenv('EMAIL')
EMAIL_PASSWORD = os.getenv('EMAIL_PASSWORD')

if not API_KEY:
    raise ValueError('Environment variable WEATHER_API_KEY is not set')

if not EMAIL:
    raise ValueError('Environment variable EMAIL is not set')

if not EMAIL_PASSWORD:
    raise ValueError('Environment variable EMAIL_PASSWORD is not set')


class Condition(BaseModel):
    text: str
    icon: str
    code: int


class DayForecast(BaseModel):
    date: str
    maxtemp_c: float
    mintemp_c: float
    avgtemp_c: float
    maxwind_kph: float
    totalprecip_mm: float
    totalsnow_cm: float
    daily_will_it_rain: int
    daily_chance_of_rain: int
    daily_will_it_snow: int
    daily_chance_of_snow: int
    condition: Condition


URL = 'http://api.weatherapi.com/v1'


def get_forecast():
    res = requests.get(
        f'{URL}/forecast.json',
        params={
            'key': API_KEY,
            'q': 'Pas de la Casa',
            'days': 7,
        },
    )
    res.raise_for_status()
    data = res.json()
    return [
        DayForecast(**day['day'], date=day['date'])
        for day in data['forecast']['forecastday']
    ]


def send_email(snow: bool, body: str):
    reciever_emails = [
        'jcalafat97@gmail.com',
    ]

    message = MIMEMultipart()
    message['From'] = EMAIL
    message['To'] = ', '.join(reciever_emails)
    message['Subject'] = f"Snow Alert! 🌨️ {'It will' if snow else 'No'} snow in the next 7 days {'🥳' if snow else '🫤'}"
    message.attach(MIMEText(body, 'plain'))

    with smtplib.SMTP('smtp.gmail.com', 587) as server:
        server.starttls()
        server.login(EMAIL, EMAIL_PASSWORD)
        for reciever_email in reciever_emails:
            server.sendmail(EMAIL, reciever_email, message.as_string())


def will_it_snow():
    days = get_forecast()
    snowing_days = [
        day for day in days
        if day.daily_will_it_snow == 1 or
        day.daily_chance_of_snow > 50
    ]
    send_email(
        bool(snowing_days),
        json.dumps([day.model_dump() for day in days], indent=2)
    )


schedule.every().day.at("08:00").do(will_it_snow)
schedule.every().day.at("20:00").do(will_it_snow)


if __name__ == '__main__':
    while True:
        schedule.run_pending()
        time.sleep(1)
