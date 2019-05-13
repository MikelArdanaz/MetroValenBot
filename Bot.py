import telebot  # Librería de la API del bot.
from telebot import types  # Tipos para la API del bot.
import requests
import json
from Token import TOKEN
from math import cos, asin, sqrt
from datetime import datetime
import pandas as pd

bot = telebot.TeleBot(TOKEN)


@bot.message_handler(commands=['start'])
def send_welcome(message):
    bot.reply_to(message, "Bienvenido a bordo!")
    bot.send_document(message.chat.id, 'https://tenor.com/Lmz1.gif')
    markup = types.ReplyKeyboardMarkup()
    itembtn1 = types.KeyboardButton('Balance')
    locstations = types.KeyboardButton('Ruta', request_location=True)
    ruta = types.KeyboardButton('Ruta')
    itembtn3 = types.KeyboardButton('Buy me a ticket!')
    if message.chat.type == 'private':
        markup.add(itembtn1, locstations, itembtn3)
    else:
        markup.add(itembtn1, ruta, itembtn3)
    bot.send_message(message.chat.id, "Elige alguna opción", reply_markup=markup)


@bot.message_handler(func=lambda message: message.text == "Balance")
def command_text_hi(message):
    msg = bot.reply_to(message, 'Introduce los primeros 10 dígitos de tu tarjeta Móbilis')
    bot.register_next_step_handler(msg, numerotarjeta)


@bot.message_handler(content_types=['location'])
def command_text_hi(message):
    stops = pd.read_csv('stops.txt')[['stop_id', 'stop_name', 'stop_lat', 'stop_lon']]
    print(closest(stops.to_dict('records'), message.location)['stop_name'])
    bot.send_message(message.chat.id,
                     'Tu estación más cercana es: ' + closest(stops.to_dict('records'), message.location)['stop_name'])
    # https://stackoverflow.com/questions/26716616/convert-a-pandas-dataframe-to-a-dictionary


@bot.message_handler(func=lambda message: message.text == "Buy me a ticket!")
def command_text_hi(message):
    bot.send_message(message.chat.id,
                     'Este es un bot gratuito. Sin embargo sería un bonito detalle que entrarás en paypal.me/mikelillo1 y me ayudaras a cargar la TUiN')
    bot.send_document(message.chat.id, 'https://tenor.com/Pw3S.gif')


@bot.message_handler(func=lambda message: message.text == "Ruta")
def command_text_hi(message):
    msg = bot.reply_to(message, 'Introduce la estación de origen')
    bot.register_next_step_handler(msg, destino)


def destino(message):
    try:
        response = requests.get("https://metrovlcschedule.herokuapp.com/api/v1/stations/converter/" + message.text)
        a = response.content.decode("utf-8")
        stations = json.loads(a)
        print(stations)
        # bot.send_message(message.chat.id, 'Estación ' + str(stations['station_code']))
        msg2 = bot.reply_to(message, 'Introduce la estación de destino')
        bot.register_next_step_handler(msg2, ruta, stations['station_code'])
    except Exception:
        print(Exception)
        bot.reply_to(message, 'oooops Salió Mal :(')


def ruta(message, origen):
    try:
        response = requests.get("https://metrovlcschedule.herokuapp.com/api/v1/stations/converter/" + message.text)
        a = response.content.decode("utf-8")
        stations = json.loads(a)
        print(stations)
        fecha = datetime.fromtimestamp(message.date)
        print(fecha)
        response = requests.get(
            "https://metrovlcschedule.herokuapp.com/api/v1/routes?from=" + str(origen) + '&to=' + str(
                stations['station_code']) + "&date=" + fecha.date().strftime('%d/%m/%Y') + "&ihour=" + str(
                fecha.time())[:5] + "&fhour=23:59")
        a = response.content.decode("utf-8")
        horario = json.loads(a)
        print(horario['journey'][0]['journeyFromStation'])
        if len(horario['journey']) > 1:
            bot.send_message(message.chat.id, 'Tienes que coger ' + str(
                len(horario['journey'])) + ' trenes. Con una duración total de: ' + str(
                horario['duration']) + 'minutos')
            for i in range(0, len(horario['journey'])):
                bot.send_message(message.chat.id, 'Tren ' + str(i + 1) + 'de' + str(
                    horario['journey'][i]['journeyFromStation']) + 'a ' + str(
                    horario['journey'][i]['journeyToStation']))
                bot.send_message(message.chat.id, 'Sus horarios son: ' + str(horario['journey'][i]['journeyHours']))
        else:
            bot.send_message(message.chat.id, 'Tienes que coger 1 tren de ' + str(
                horario['journey'][0]['journeyFromStation']) + + 'a ' + str(
                horario['journey'][0]['journeyToStation']) + 'Con una duración total de: ' + str(
                horario['duration']) + 'minutos')
            bot.send_message(message.chat.id, 'Tren de: ' + str(horario['journey'][0]['journeyHours']))
    except Exception:
        print(Exception)
        bot.reply_to(message, 'oooops Salió Mal :(')


def numerotarjeta(message):
    try:
        response = requests.get("https://metrovlcschedule.herokuapp.com/api/v1/card/" + message.text + "/balance")
        a = response.content.decode("utf-8")
        tarjeta = json.loads(a)
        print(a)
        bot.send_message(message.chat.id, 'Tu tarjeta: ' + tarjeta['cardZones'])
        bot.send_message(message.chat.id, 'Tiene un saldo de: ' + tarjeta['cardBalance'])
    except Exception:
        bot.reply_to(message, 'oooops Salió Mal :(')


def distance(lat1, lon1, lat2, lon2):
    """
    Calculates closest latitude and longitude using the Haversine formula. For more information, take a look at:
    https://stackoverflow.com/questions/41336756/find-the-closest-latitude-and-longitude
    :param lat1:
    :param lon1:
    :param lat2:
    :param lon2:
    :return:
    """
    p = 0.017453292519943295
    a = 0.5 - cos((lat2 - lat1) * p) / 2 + cos(lat1 * p) * cos(lat2 * p) * (1 - cos((lon2 - lon1) * p)) / 2
    return 12742 * asin(sqrt(a))


def closest(stations, location):
    return min(stations,
               key=lambda stat: distance(location.latitude, location.longitude, stat['stop_lat'], stat['stop_lon']))


bot.polling()
