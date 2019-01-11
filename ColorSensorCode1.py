#############################
#Washing Machine Sensor Code#
#############################

import RPi.GPIO as GPIO
import time
import requests
import os
import socket
import fcntl
import struct
import time
from time import gmtime, strftime


# Defining GPIO pins configuration
s2 = 20
s3 = 16
signal = 21

washingMachine2_s2 = 0
washingMachine2_s3 = 5
washingMachine2_signal = 6

NUM_CYCLES = 10
redPin = 13
greenPin = 19
bluePin = 26

## Define GPIO to LCD mapping
LCD_RS = 7
LCD_E  = 8
LCD_D4 = 25
LCD_D5 = 24
LCD_D6 = 23
LCD_D7 = 18

# Define some device constants
LCD_WIDTH = 16    # Maximum characters per line
LCD_CHR = True
LCD_CMD = False

LCD_LINE_1 = 0x80 # LCD RAM address for the 1st line
LCD_LINE_2 = 0xC0 # LCD RAM address for the 2nd line

# Timing constants
E_PULSE = 0.0005
E_DELAY = 0.0005


# Defining the api-endpoint 
API_ENDPOINT = "https://washingmachineserverke7.herokuapp.com/machineStatus"


def setup():
  print("Setting GPIO Pins\n")
  GPIO.setmode(GPIO.BCM)
  GPIO.setwarnings(False)

  GPIO.setup(signal,GPIO.IN, pull_up_down=GPIO.PUD_UP)
  GPIO.setup(s2,GPIO.OUT)
  GPIO.setup(s3,GPIO.OUT)

  
  GPIO.setup(washingMachine2_signal,GPIO.IN, pull_up_down=GPIO.PUD_UP)
  GPIO.setup(washingMachine2_s2,GPIO.OUT)
  GPIO.setup(washingMachine2_s3,GPIO.OUT)

  GPIO.setup(redPin, GPIO.OUT)
  GPIO.setup(greenPin, GPIO.OUT)
  GPIO.setup(bluePin, GPIO.OUT)

  # Setting up GPIO pins for LCD
  GPIO.setup(LCD_E, GPIO.OUT)  # E
  GPIO.setup(LCD_RS, GPIO.OUT) # RS
  GPIO.setup(LCD_D4, GPIO.OUT) # DB4
  GPIO.setup(LCD_D5, GPIO.OUT) # DB5
  GPIO.setup(LCD_D6, GPIO.OUT) # DB6
  GPIO.setup(LCD_D7, GPIO.OUT) # DB7

  print("Initializing display")
  # Initialise display
  lcd_init()


def detectRed(s2, s3, signal) :
  GPIO.output(s2,GPIO.LOW)
  GPIO.output(s3,GPIO.LOW)
  time.sleep(0.3)
  start = time.time()
  for impulse_count in range(NUM_CYCLES):
    GPIO.wait_for_edge(signal, GPIO.FALLING)
  duration = time.time() - start 
  red  = NUM_CYCLES / duration
  return red


def detectBlue(s2, s3, signal):
  GPIO.output(s2,GPIO.LOW)
  GPIO.output(s3,GPIO.HIGH)
  time.sleep(0.3)
  start = time.time()
  for impulse_count in range(NUM_CYCLES):
    GPIO.wait_for_edge(signal, GPIO.FALLING)
  duration = time.time() - start
  blue = NUM_CYCLES / duration
  return blue


def detectGreen(s2, s3, signal): 
  GPIO.output(s2,GPIO.HIGH)
  GPIO.output(s3,GPIO.HIGH)
  time.sleep(0.3)
  start = time.time()
  for impulse_count in range(NUM_CYCLES):
    GPIO.wait_for_edge(signal, GPIO.FALLING)
  duration = time.time() - start
  green = NUM_CYCLES / duration
  return green

  
    
def detectColor(s2, s3, signal):

  red = detectRed(s2, s3, signal)
  blue = detectBlue(s2, s3, signal)
  green = detectGreen(s2, s3, signal)
  
  if green < red and blue < red :
    return "RED"

  elif red < green and blue < green :
    return "GREEN"

  elif green < blue and red < blue :
    return "BLUE"
    
      
def getCorrectColor(s2, s3, signal):
  
  objectColorDict = {}
  
  for i in range(20):
    color = detectColor(s2, s3, signal)
    if color in objectColorDict :
      objectColorDict[color] += 1
    else :
      objectColorDict[color] = 1

  correctColor = max(objectColorDict.keys(), key = (lambda k : objectColorDict[k]))
  print("Color detected : " + correctColor)
  return correctColor      

def lightLED(color):
  if color == "RED" :
    GPIO.output(redPin, GPIO.LOW)
    GPIO.output(greenPin, GPIO.HIGH)
    GPIO.output(bluePin, GPIO.HIGH)
    
  elif color == "GREEN" :
    GPIO.output(greenPin, GPIO.LOW)
    GPIO.output(redPin, GPIO.HIGH)
    GPIO.output(bluePin, GPIO.HIGH)

  elif color == "BLUE" :
    GPIO.output(bluePin, GPIO.LOW)
    GPIO.output(redPin, GPIO.HIGH)
    GPIO.output(greenPin, GPIO.HIGH)
    
def loop():

  while(1):
    sensorColorDetection(s2, s3, signal, 1)
    sensorColorDetection(washingMachine2_s2, washingMachine2_s3, washingMachine2_signal, 2)
    
    time.sleep(0.3)

def sensorColorDetection(s2, s3, signal, sensorNumber) :
    print("Sensing color of object from sensor " + str(sensorNumber))
    color = getCorrectColor(s2, s3, signal)
    lcd_string("Color detected :",LCD_LINE_1)
    lcd_string(color,LCD_LINE_2)
    sendPostRequest(color , sensorNumber)
    lightLED(color)

def sendPostRequest(color, machineNumber):

  # Defining data packets
  dataON = { "block" : "GH",
           "machineId" : str(machineNumber),
           "machineStatus" : "Available",
           "machineBackgroundColor" : "green",
           "text" : "Washing Machine " + str(machineNumber)
         }

  dataOFF = { "block" : "GH",
              "machineId" : str(machineNumber),
              "machineStatus" : "Unavailable",
              "machineBackgroundColor" : "red",
              "text" : "Washing Machine " + str(machineNumber)
            }

  print(dataON)
  print(dataOFF)
  if color == "RED" :
    print("Washing machine available")
    response = requests.post(url = API_ENDPOINT, data = dataON) 

  else :    
    print("Washing machine unavailable")
    response = requests.post(url = API_ENDPOINT, data = dataOFF) 
        
  message = response.text 
  print("The response message is: %s"%message)    

def lcd_init():
  # Initialise display
  lcd_byte(0x33,LCD_CMD) # 110011 Initialise
  lcd_byte(0x32,LCD_CMD) # 110010 Initialise
  lcd_byte(0x06,LCD_CMD) # 000110 Cursor move direction
  lcd_byte(0x0C,LCD_CMD) # 001100 Display On,Cursor Off, Blink Off
  lcd_byte(0x28,LCD_CMD) # 101000 Data length, number of lines, font size
  lcd_byte(0x01,LCD_CMD) # 000001 Clear display
  time.sleep(E_DELAY)

def lcd_toggle_enable():
  # Toggle enable
  time.sleep(E_DELAY)
  GPIO.output(LCD_E, True)
  time.sleep(E_PULSE)
  GPIO.output(LCD_E, False)
  time.sleep(E_DELAY)

def lcd_byte(bits, mode):
  # Send byte to data pins
  # bits = data
  # mode = True  for character
  #        False for command

  GPIO.output(LCD_RS, mode) # RS

  # High bits
  GPIO.output(LCD_D4, False)
  GPIO.output(LCD_D5, False)
  GPIO.output(LCD_D6, False)
  GPIO.output(LCD_D7, False)
  if bits&0x10==0x10:
    GPIO.output(LCD_D4, True)
  if bits&0x20==0x20:
    GPIO.output(LCD_D5, True)
  if bits&0x40==0x40:
    GPIO.output(LCD_D6, True)
  if bits&0x80==0x80:
    GPIO.output(LCD_D7, True)

  # Toggle 'Enable' pin
  lcd_toggle_enable()

  # Low bits
  GPIO.output(LCD_D4, False)
  GPIO.output(LCD_D5, False)
  GPIO.output(LCD_D6, False)
  GPIO.output(LCD_D7, False)
  if bits&0x01==0x01:
    GPIO.output(LCD_D4, True)
  if bits&0x02==0x02:
    GPIO.output(LCD_D5, True)
  if bits&0x04==0x04:
    GPIO.output(LCD_D6, True)
  if bits&0x08==0x08:
    GPIO.output(LCD_D7, True)

  # Toggle 'Enable' pin
  lcd_toggle_enable()


def lcd_string(message,line):
  # Cast to string
  message = str(message)
  # Send string to display
  message = message.ljust(LCD_WIDTH," ")

  lcd_byte(line, LCD_CMD)

  for i in range(LCD_WIDTH):
    lcd_byte(ord(message[i]),LCD_CHR)
  
def endprogram():
    GPIO.cleanup()

if __name__=='__main__':
    
    setup()

    try:
        loop()

    except KeyboardInterrupt:
        endprogram()
