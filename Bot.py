import telebot  # Librería de la API del bot.
from telebot import types  # Tipos para la API del bot.
import requests
import json
from Token import TOKEN
bot = telebot.TeleBot(TOKEN)


@bot.message_handler(commands=['start'])
def send_welcome(message):
    bot.reply_to(message, "Bienvenido a bordo!")
    bot.send_document(message.chat.id, 'https://tenor.com/Lmz1.gif')
    markup = types.ReplyKeyboardMarkup()
    itembtn1 = types.KeyboardButton('Balance')
    itembtn2 = types.KeyboardButton('Estaciones')
    itembtn3 = types.KeyboardButton('Buy me a ticket!')
    markup.add(itembtn1, itembtn2,itembtn3)
    bot.send_message(message.chat.id, "Elige alguna opción", reply_markup=markup)


@bot.message_handler(func=lambda message: message.text == "Balance")
def command_text_hi(message):
    msg = bot.reply_to(message, 'Introduce los primeros 10 dígitos de tu tarjeta Móbilis')
    bot.register_next_step_handler(msg, numerotarjeta)


@bot.message_handler(func=lambda message: message.text == "Estaciones")
def command_text_hi(message):
    response = requests.get("https://metrovlcschedule.herokuapp.com/api/v1/stations")
    a = response.content.decode("utf-8")
    stations = json.loads(a)
    bot.send_message(message.chat.id, 'Estaciones ' + str(stations.values()))


@bot.message_handler(func=lambda message: message.text == "Buy me a ticket!")
def command_text_hi(message):
    bot.send_message(message.chat.id, 'Este es un bot gratuito. Sin embargo sería un bonito detalle que entrarás en paypal.me/mikelillo1 y me ayudaras a cargar la TUiN')
    bot.send_document(message.chat.id, 'https://tenor.com/Pw3S.gif')

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


bot.polling()
