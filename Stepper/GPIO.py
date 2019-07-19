import RPi.GPIO as GPIO
from time import sleep
import numpy as np
import pigpio

"""
functions:



def initGPIO(*args,**kwargs):
    
    initializes GPIO pins
    
initGPIO()
    initialize GPIO pins

cleanGPIO()
    cleans GPIO pins

step_pulse()
    gives the signal for a step
    
set_mode()
    set BCM or BOARD
set_dir()
    sets the direction

move_periodPWM()
    
    moves the motor with pigpio PWM
    
"""



def initGPIO(*args,**kwargs):

    mode=kwargs["mode"]
    
    
    if mode == "BCM":
        GPIO.setmode(GPIO.BCM)
    else:
        GPIO.setmode(GPIO.BOARD)
   
    for port in args:
        
        GPIO.setup(port, GPIO.OUT)
        


def cleanGPIO():
    GPIO.cleanup()
    
def step_pulse(delay,step_pin):

    GPIO.output(step_pin, GPIO.HIGH)
    sleep(delay)
    GPIO.output(step_pin, GPIO.LOW)


def set_mode(modetuple,mode):
    

    GPIO.output(modetuple, mode)
    

def setdir(dir,dirpin):
    
    GPIO.output(dirpin,GPIO.HIGH if dir else GPIO.LOW)
    


def move_periodPWM(motor, step_pin, dir_pin, frequency, step_count, dir, wf, mode):
    setdir(dir, dir_pin)
    p = GPIO.PWM(step_pin, frequency * step_count * 2)
    p.start(50)

    if wf == "tri":
        for step in range(step_count):
            sleep(.5 / (frequency * step_count))
            motor.position += 1 / motor.steps_per_rev if dir else -1/motor.steps_per_rev




    else:
        for step in range(step_count):
            dutycycle = 100 * np.sin((np.pi * step) / step_count)
            p.ChangeDutyCycle(dutycycle)
            sleep(.5 / (frequency * step_count))
            motor.position += 1 / motor.steps_per_rev

    p.stop()
    

