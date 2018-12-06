import RPi.GPIO as GPIO
import time
import requests

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


  
def endprogram():
    GPIO.cleanup()

if __name__=='__main__':
    
    setup()

    try:
        loop()

    except KeyboardInterrupt:
        endprogram()
