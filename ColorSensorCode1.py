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
NUM_CYCLES = 10
redPin = 13
greenPin = 19
bluePin = 26
PIRPin = 4
VIBPin = 15

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

# Defining data packets
dataON = { "block" : "GH",
         "machineId" : "1",
         "machineStatus" : "Available",
         "machineBackgroundColor" : "green",
         "text" : "Washing Machine 1"
       }

dataOFF = { "block" : "GH",
            "machineId" : "1",
            "machineStatus" : "Unavailable",
            "machineBackgroundColor" : "red",
            "text" : "Washing Machine 1"
          }

def setup():
  print("Setting GPIO Pins\n")
  GPIO.setmode(GPIO.BCM)
  GPIO.setup(signal,GPIO.IN, pull_up_down=GPIO.PUD_UP)
  GPIO.setup(s2,GPIO.OUT)
  GPIO.setup(s3,GPIO.OUT)
  GPIO.setup(redPin, GPIO.OUT)
  GPIO.setup(greenPin, GPIO.OUT)
  GPIO.setup(bluePin, GPIO.OUT)
  GPIO.setup(PIRPin, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)
  GPIO.setup(VIBPin, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)

  # Setting up GPIO pins for LCD
  GPIO.setwarnings(False)
  GPIO.setmode(GPIO.BCM)       # Use BCM GPIO numbers
  GPIO.setup(LCD_E, GPIO.OUT)  # E
  GPIO.setup(LCD_RS, GPIO.OUT) # RS
  GPIO.setup(LCD_D4, GPIO.OUT) # DB4
  GPIO.setup(LCD_D5, GPIO.OUT) # DB5
  GPIO.setup(LCD_D6, GPIO.OUT) # DB6
  GPIO.setup(LCD_D7, GPIO.OUT) # DB7

  print("Initializing display")
  # Initialise display
  lcd_init()


def detectRed() :
  GPIO.output(s2,GPIO.LOW)
  GPIO.output(s3,GPIO.LOW)
  time.sleep(0.3)
  start = time.time()
  for impulse_count in range(NUM_CYCLES):
    GPIO.wait_for_edge(signal, GPIO.FALLING)
  duration = time.time() - start 
  red  = NUM_CYCLES / duration
  return red


def detectBlue():
  GPIO.output(s2,GPIO.LOW)
  GPIO.output(s3,GPIO.HIGH)
  time.sleep(0.3)
  start = time.time()
  for impulse_count in range(NUM_CYCLES):
    GPIO.wait_for_edge(signal, GPIO.FALLING)
  duration = time.time() - start
  blue = NUM_CYCLES / duration
  return blue


def detectGreen(): 
  GPIO.output(s2,GPIO.HIGH)
  GPIO.output(s3,GPIO.HIGH)
  time.sleep(0.3)
  start = time.time()
  for impulse_count in range(NUM_CYCLES):
    GPIO.wait_for_edge(signal, GPIO.FALLING)
  duration = time.time() - start
  green = NUM_CYCLES / duration
  return green

  
    
def detectColor():

  red = detectRed()
  blue = detectBlue()
  green = detectGreen()
  
  if green < red and blue < red :
    #print("Red object detected")
    return "RED"

  elif red < green and blue < green :
    #print("Green object detected")
    return "GREEN"

  elif green < blue and red < blue :
    #print("Blue object detected")
    return "BLUE"
    
      
def getCorrectColor():

  print("Sensing color of object...")
  
  objectColorDict = {}
  
  for i in range(20):
    color = detectColor()
    #lightLED(color)
    #print("Color detected is " + color)
    if color in objectColorDict :
      objectColorDict[color] += 1

    else :
      objectColorDict[color] = 1

  print(objectColorDict)
  correctColor = max(objectColorDict.keys(), key = (lambda k : objectColorDict[k]))
  print("Correct color detected : " + correctColor)
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

def detectMovement() :
  i = GPIO.input(PIRPin)
  if i == 0 :
    print("No movement detected")
  else : 
    print("Movement detected")

def detectVibration() :
  v = GPIO.input(VIBPin)
  if v == 0 :
    print("No vibration detected")
  else :
    print("Vibration detected")
    
def loop():

  while(1):
    color = getCorrectColor()
    lcd_string("Color detected :",LCD_LINE_1)
    lcd_string(color,LCD_LINE_2)
    sendPostRequest(color)
    lightLED(color)
    detectMovement()
    detectVibration()
    time.sleep(0.3)


def sendPostRequest(color):

  if color == "RED" :

    print("Washing machine available")
    print("Sending ON post request")
    
    response = requests.post(url = API_ENDPOINT, data = dataON) 

  else :
    
    print("Washing machine unavailable")
    print("Sending OFF post request")

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
