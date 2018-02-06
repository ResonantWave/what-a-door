#!/usr/bin/env python
# -*- coding: utf-8 -*-

import time
import os
import logging

import RPI.GPIO as GPIO
import Adafruit_DHT
import telebot

from telebot import types
from PIL     import Image

logger = telebot.logger
door = telebot.TeleBot("") # your bot id goes here
sensor = Adafruit_DHT.DHT11

telebot.logger.setLevel(logging.DEBUG)

GPIO.setmode(GPIO.BCM)
GPIO.setup(18, GPIO.OUT)
GPIO.setup(23, GPIO.IN, pull_up_down = GPIO.PUD_DOWN)

GPIO.output(18, 1)

time_ignore = 5*60
allowed_numbers = 0000, 0000 # list of allowed users
tempPin = 24
active = True

@door.message_handler(commands=['start'])
def handle_start_help(m):
   """Sends custom keyboard to user"""

   if (int(time.time()) - time_ignore) > m.date:
      return

   door.send_chat_action(m.chat.id, 'typing')
   markup = types.ReplyKeyboardMarkup()
   itembtn1 = types.KeyboardButton('/open')
   itembtn2 = types.KeyboardButton('/pic')
   markup.row(itembtn1, itembtn2)
   itembtn3 = types.KeyboardButton('/temp')
   markup.row(itembtn3)
   itembtn4 = types.KeyboardButton('/monitor')
   itembtn5 = types.KeyboardButton('/stopmonitor')
   markup.row(itembtn4, itembtn5)

   door.send_message(m.chat.id, 'Please choose an action. ' + str(m.chat.id), reply_markup = markup) # reply with user ID on /start

@door.message_handler(commands=['open'])
def open_portal(m):
   """Activates a relay on GPIO pin 18 for 3 seconds"""

   if (int(time.time()) - time_ignore) > m.date:
      return

   if(m.chat.id in allowed_numbers):
      door.send_chat_action(m.chat.id, 'typing')
      door.send_message(m.chat.id, 'Door opened')

      GPIO.output(18, 0)
      time.sleep(3)
      GPIO.output(18, 1)

@door.message_handler(commands=['pic'])
def take_pic(m):
   """Takes a picture with the Raspberry Pi camera,
   crops it and sends it to the user
   """

   if (int(time.time()) - time_ignore) > m.date:
      return

   if(m.chat.id in allowed_numbers):
      door.send_chat_action(m.chat.id, 'upload_photo')
      os.system('raspistill -o /home/pi/pic.jpg -t 1')
      toCrop = Image.open('/home/pi/pic.jpg')

      half_the_width = toCrop.size[0] / 2
      half_the_height = toCrop.size[1] / 2
      img = toCrop.crop( # manual cropping to fit desired area
         (half_the_width - 400,
          half_the_height - 60,
          half_the_width + 300,
          half_the_height + 640)
      )
      img.save('/home/pi/picCrop.jpg')

      photo = open('/home/pi/picCrop.jpg', 'rb')
      door.send_photo(m.chat.id, photo)
      photo.close()

@door.message_handler(commands=['temp'])
def temperature(m):
   """Reads DHT11 temperature sensor and sends data to user"""

   if (int(time.time()) - time_ignore) > m.date:
      return

   if(m.chat.id in allowed_numbers):
      door.send_chat_action(m.chat.id, 'typing')
      humidity, temperature = Adafruit_DHT.read_retry(sensor, tempPin)
      door.send_message(m.chat.id, 'Temp = {0:0.01f}ºC  Humidity = {1:0.01f}%'.format(temperature, humidity))

@door.message_handler(commands=['keepopen'])
def keep_open(m):
   """Keeps the relay on pin 18 active until manually turned off"""

   if (int(time.time()) - time_ignore) > m.date:
      return

   if(m.chat.id in allowed_numbers):
      door.send_chat_action(m.chat.id, 'typing')
      door.send_message(m.chat.id, 'Door will be kept opened until further indicated')

      GPIO.output(18, 1)

@door.message_handler(commands=['close'])
def close(m):
   """Turns off relay on pin 18"""

   if (int(time.time()) - time_ignore) > m.date:
      return

   if(m.chat.id in allowed_numbers):
      door.send_chat_action(m.chat.id, 'typing')
      door.send_message(m.chat.id, 'Door closed')

      GPIO.output(18, 0)

@door.message_handler(commands=['monitor'])
def monitor(m):
   """Checks for intruders with a magnetic reed switch on pin 23.

      If trespassing is detected, pictures are taken and sent until
      the sensor is inactive again.
   """
   if (int(time.time()) - time_ignore) > m.date:
      return

   if(m.chat.id in allowed_numbers):
      door.send_message(m.chat.id, 'Door monitor enabled')
      global active
      active = True

      while active:
         if(GPIO.input(23) == 0):
            door.send_message(m.chat.id, 'Someone has entered!')
            os.system('raspistill -o /home/pi/pic.jpg -t 1')
            toCrop = Image.open('/home/pi/pic.jpg')

            half_the_width = toCrop.size[0] / 2
            half_the_height = toCrop.size[1] / 2
            img = toCrop.crop(
               (half_the_width - 400,
                half_the_height - 60,
                half_the_width + 300,
                half_the_height + 640)
            )
            img.save('/home/pi/picCrop.jpg')

            photo = open('/home/pi/picCrop.jpg', 'rb')
            door.send_photo(m.chat.id, photo)
            photo.close()
         time.sleep(2)

@door.message_handler(commands=['stopmonitor'])
def stop_monitor(m):
   """Disables intruder checking"""

   if (int(time.time()) - time_ignore) > m.date:
      return

   if(m.chat.id in allowed_numbers):
      door.send_message(m.chat.id, 'Door monitor disabled')
      global active
      active = False

door.polling(none_stop = True)

