import RPi.GPIO as GPIO
import time
import requests

# Defining GPIO pins configuration
s2 = 23
s3 = 24
signal = 25
NUM_CYCLES = 10
redPin = 8
greenPin = 7
bluePin = 1

# Defining the api-endpoint 
API_ENDPOINT = "https://washingmachineserverke7.herokuapp.com/machineStatus"

def setup():
  print("Setting GPIO Pins\n")
  GPIO.setmode(GPIO.BCM)
  GPIO.setup(signal,GPIO.IN, pull_up_down=GPIO.PUD_UP)
  GPIO.setup(s2,GPIO.OUT)
  GPIO.setup(s3,GPIO.OUT)
  GPIO.setup(redPin, GPIO.OUT)
  GPIO.setup(greenPin, GPIO.OUT)
  GPIO.setup(bluePin, GPIO.OUT)

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

    
def loop():

  while(1):
    color = getCorrectColor()
    sendPostRequest(color)
    lightLED(color)


def sendPostRequest(color):

  if color == "GREEN" :

    print("Washing machine available")
    # data to be sent to api 
    data = { "machineName" : "WashingMachine1",
           "machineStatus" : "ON"
         }
        
    # sending post request and saving response as response object 
    response = requests.post(url = API_ENDPOINT, data = data) 

    # extracting response text 
    message = response.text 
    print("The response message is: %s"%message)

  else :
    print("Washing machine unavailable")
        
        
  
def endprogram():
    GPIO.cleanup()

if __name__=='__main__':
    
    setup()

    try:
        loop()

    except KeyboardInterrupt:
        endprogram()
