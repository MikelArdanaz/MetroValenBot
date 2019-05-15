import json
from datetime import datetime
from math import cos, asin, sqrt

import pandas as pd
import requests
import telebot  # Librería de la API del bot.
import os
from telebot import types  # Tipos para la API del bot.
import pytz

TOKEN = os.getenv("TOKEN")
bot = telebot.TeleBot(TOKEN)
Mobilis = {}


@bot.message_handler(commands=['start'])
def send_welcome(message):
    bot.reply_to(message, "Bienvenido a bordo!")
    bot.send_document(message.chat.id, 'https://tenor.com/Lmz1.gif')
    markup = types.ReplyKeyboardMarkup()
    balance = types.KeyboardButton('Balance')
    locstations = types.KeyboardButton('Ruta (Ubicación)', request_location=True)
    ruta = types.KeyboardButton('Ruta (Manual)')
    cremaets = types.KeyboardButton('Buy me a ticket!')
    plano = types.KeyboardButton('Planos')
    about = types.KeyboardButton('About')
    borrar = types.KeyboardButton('Olvidar mi Móbilis')
    if message.chat.type == 'private':
        markup.add(balance, locstations, ruta, cremaets, plano, about, borrar)
    else:
        markup.add(balance, ruta, cremaets, plano, about, borrar)
    bot.send_message(message.chat.id, "Elige alguna opción", reply_markup=markup)


@bot.message_handler(func=lambda message: message.text == "Balance")
def command_text_hi(message):
    if message.from_user.id in Mobilis:
        numerotarjeta(message, tarjeta=Mobilis[message.from_user.id])
    else:
        msg = bot.reply_to(message, 'Introduce los primeros 10 dígitos de tu tarjeta Móbilis')
        bot.register_next_step_handler(msg, numerotarjeta)


@bot.message_handler(func=lambda message: message.text == "Planos")
def command_text_hi(message):
    doc = open('PlanoGeneral_Metrovalencia_2018.pdf', 'rb')
    bot.send_document(message.chat.id, doc)
    doc = open('PlanoRed_Metrovalencia_2018.pdf', 'rb')
    bot.send_document(message.chat.id, doc)


@bot.message_handler(func=lambda message: message.text == "Olvidar mi Móbilis")
def command_text_hi(message):
    if message.from_user.id in Mobilis:
        Mobilis.pop(message.from_user.id)
        bot.send_message(message.chat.id, 'Móbilis olvidada!')
    else:
        bot.send_message(message.chat.id, 'No habías añadido ninguna Móbilis. Tú lo que quieres es volverme loco')
        bot.send_document(message.chat.id, 'https://tenor.com/vNpv.gif')


@bot.message_handler(func=lambda message: message.text == "About")
def command_text_hi(message):
    bot.send_message(message.chat.id,
                     'Este Bot ha sido desarrollado por Maria Bellver, Alejandro Sanz y [Mikel Ardanaz]'
                     '(twitter.com/mikelillo_1)\nSu código se encuentra en este repositorio de '
                     '[GitHub](https://github.com/MikelArdanaz/TrabajoMLI)\nEn su desarrollo hemos usado la maravillosa'
                     ' [API](http://metrovlcschedule.tk) (no oficial) de Metrovalencia desarrollada por '
                     '[Cristian Molina](https://github.com/legomolina)',
                     parse_mode='Markdown')


@bot.message_handler(content_types=['location'])
def command_text_hi(message):
    stops = pd.read_csv('stops.txt')[['stop_id', 'stop_name', 'stop_lat', 'stop_lon']]
    nearest = closest(stops.to_dict('records'), message.location)
    bot.send_message(message.chat.id,
                     'Tu estación más cercana es: ' + nearest['stop_name'])
    msg2 = bot.reply_to(message, 'Introduce la estación de destino')
    bot.register_next_step_handler(msg2, ruta, nearest['stop_id'])
    # https://stackoverflow.com/questions/26716616/convert-a-pandas-dataframe-to-a-dictionary


@bot.message_handler(func=lambda message: message.text == "Buy me a ticket!")
def command_text_hi(message):
    bot.send_message(message.chat.id,
                     text='Este es un bot gratuito. Sin embargo sería un bonito detalle (guiño,guiño)'
                          ' que entrarás en paypal.me/mikelillo1 y me ayudaras a cargar la TUiN.')
    bot.send_document(message.chat.id, 'https://tenor.com/Pw3S.gif')


@bot.message_handler(func=lambda message: message.text == "Ruta (Manual)")
def command_text_hi(message):
    msg = bot.reply_to(message, 'Introduce la estación de origen')
    bot.register_next_step_handler(msg, destino)


def destino(message):
    try:
        response = requests.get("https://metrovlcschedule.herokuapp.com/api/v1/stations/converter/" + message.text)
        a = response.content.decode("utf-8")
        stations = json.loads(a)
        msg2 = bot.reply_to(message, 'Introduce la estación de destino')
        bot.register_next_step_handler(msg2, ruta, stations['station_code'])
    except Exception as e:
        if hasattr(e, 'message'):
            print(e.message)
        else:
            print(e)
        bot.reply_to(message, 'oooops Salió Mal :(')
        bot.send_document(message.chat.id, 'https://tenor.com/qKYb.gif')


def ruta(message, origen):
    try:
        response = requests.get("https://metrovlcschedule.herokuapp.com/api/v1/stations/converter/" + message.text)
        a = response.content.decode("utf-8")
        stations = json.loads(a)
        fecha = datetime.fromtimestamp(message.date).astimezone(pytz.timezone('Europe/Madrid'))
        response = requests.get(
            "https://metrovlcschedule.herokuapp.com/api/v1/routes?from=" + str(origen) + '&to=' + str(
                stations['station_code']) + "&date=" + fecha.date().strftime(
                '%d/%m/%Y') + "&ihour=" + str(fecha.hour) + ':' + a.strftime('%M')
            + "&fhour=23:59")
        a = response.content.decode("utf-8")
        horario = json.loads(a)
        print('Hora'+str(fecha.hour))
        print('Minutos:'+str(fecha.minute))
        if len(horario['journey']) > 1:
            bot.send_message(message.chat.id, 'Tienes que coger ' + str(
                len(horario['journey'])) + ' trenes. Con una duración total de: ' + str(
                horario['duration']) + ' minutos')
            for i in range(0, len(horario['journey'])):
                response = requests.get(
                    "https://metrovlcschedule.herokuapp.com/api/v1/stations/converter/" + str(
                        horario['journey'][i]['journeyFromStation']))
                a = response.content.decode("utf-8")
                origen = json.loads(a)
                response = requests.get(
                    "https://metrovlcschedule.herokuapp.com/api/v1/stations/converter/" + str(
                        horario['journey'][i]['journeyToStation']))
                a = response.content.decode("utf-8")
                destino = json.loads(a)
                bot.send_message(message.chat.id,
                                 'Tren ' + str(i + 1) + ' de ' + origen['station_name'] + ' a ' + destino[
                                     'station_name'])
                bot.send_message(message.chat.id, 'Sus horarios son: ' + str(horario['journey'][i]['journeyHours']))
                bot.send_message(message.chat.id, 'Te sirven los trenes con destino:' + ', '.join(
                    horario['journey'][i]['journeyTrains']))
        else:
            response = requests.get(
                "https://metrovlcschedule.herokuapp.com/api/v1/stations/converter/" + str(
                    horario['journey'][0]['journeyFromStation']))
            a = response.content.decode("utf-8")
            origen = json.loads(a)
            response = requests.get(
                "https://metrovlcschedule.herokuapp.com/api/v1/stations/converter/" + str(
                    horario['journey'][0]['journeyToStation']))
            a = response.content.decode("utf-8")
            destino = json.loads(a)
            bot.send_message(message.chat.id, 'Tienes que coger 1 tren de ' + origen['station_name'] + ' a ' + destino[
                'station_name'] + '.\nCon una duración total de: ' + str(
                horario['duration']) + ' minutos')
            bot.send_message(message.chat.id, 'Tienes trenes a las: ' + str(
                horario['journey'][0]['journeyHours']))
            bot.send_message(message.chat.id, 'Te sirven los trenes con destino: ' + ', '.join(
                horario['journey'][0]['journeyTrains']))
    except Exception as e:
        if hasattr(e, 'message'):
            print(e.message)
        else:
            print(e)
        bot.reply_to(message, 'oooops Salió Mal :(')
        bot.send_document(message.chat.id, 'https://tenor.com/ylHW.gif')


def numerotarjeta(message, tarjeta=None):
    try:
        if tarjeta:
            response = requests.get("https://metrovlcschedule.herokuapp.com/api/v1/card/" + str(tarjeta) + "/balance")
            a = response.content.decode("utf-8")
            tarjeta = json.loads(a)
        else:
            response = requests.get("https://metrovlcschedule.herokuapp.com/api/v1/card/" + message.text + "/balance")
            a = response.content.decode("utf-8")
            tarjeta = json.loads(a)
            if tarjeta['cardZones']:
                Mobilis[int(message.from_user.id)] = message.text
        bot.send_message(message.chat.id, 'Tu tarjeta: ' + tarjeta['cardZones'])
        bot.send_message(message.chat.id, 'Tiene un saldo de: ' + tarjeta['cardBalance'])
    except Exception as e:
        if hasattr(e, 'message'):
            print(e.message)
        else:
            print(e)
        bot.reply_to(message, 'oooops Salió Mal :(')
        bot.send_document(message.chat.id, 'https://tenor.com/u4yf.gif')


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
