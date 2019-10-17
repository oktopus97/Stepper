from time import sleep, time
import sys,os
sys.path.append(os.getcwd())
from Stepper.tools import computeLinearDelay, configreader,get_sin_table
from Stepper.constants import  RESOLUTION_DICT
from matplotlib import pyplot as plt
import timeit
from matplotlib import pyplot as plt
import numpy as np

import Stepper.GPIO as GPIO





#from config import step_angle, dir, step, m1, m2, m3 , gpio_mode


"""
object Motor:

    config:

        step_angle
        resolution

        gpio_mode
        (PINS)
        dir
        step
        m1
        m2
        m3


    __init__:        self.adc = Adafruit_ADS1x15.ADS1015()
        reads the motor config and initializes the motor parameters

    move_one_period():
        performs an up and a down movement (mode argument is the pull or press setting TODO)

    move_steps():
        move with constant speed with the given step count. used for the movements other than the experiment like the application
        of the starting force

    INITGPIO():
        initializes GPIO ports
    cleanGPIO():
        cleans GPIO ports

object ForceSensor:

    get_reading():
        gets the reading from the sensor
"""




class Motor(object):
    """
    initialize a motor class with default position x = 0
    params:
    step_angle in Degrees(default 1.8)
    coef : step coefficient, default 1 for Full step

    RasPi pins(mode = BCM):

    dir (def = 20)
    step (def = 21)
    m1 (def = 14)
    m2 (def = 15)
    m3 (def = 18)

    """
    def __init__(self,force_sensor,test=False):
        
        self.fs=force_sensor
        
        #test variablen
        
        ##reading settings from file
        self.update_features()



        



        self.steps_per_rev = int(360/float(self.angle))*RESOLUTION_DICT[self.resolution][1]
        self.test = test
        
        self.GPIO_OUTPUTS = False
    
    def update_features(self):
        [self.gpio_mode, self.resolution,self.angle, self.dir, self.step, self.m1,self.m2,self.m3] =  configreader('gpio_mode',"resolution",'step_angle','dir',
                                                                                          'step','m1','m2','m3',category='motor_config',
                                                                                                                   file="Stepper/motorconfig.cfg")
        self.step, self.dir, self.m1, self.m2, self.m3 = int(self.step), int(self.dir),int(self.m1),int(self.m2),int(self.m3)
        self.mode = (self.m1, self.m2, self.m3)

        self.manual_speed =  int(configreader('manual motor speed (mm/s)', category='manual_config', file='Stepper/config.cfg')[0])



    def move_one_period(self, step_count, delay, mode,start):
        """
        Moves the motor one period
        :param mode: Lasttyp von der Bioreaktor 'z' 'd'  default 'd'
        :param distance: in mm positive for up negative for down
        """

        basedir = True if mode == "0" else False

        dir = basedir ##1 for down
        self.move_steps(step_count, delay,dir,start)
        #GPIO.move_periodPWM(self, self.step, self.dir, frequency, step_count, dir,waveform, mode)



        dir = not basedir
        self.move_steps(step_count, delay,dir,start,reverse_delays=True)

        #GPIO.move_periodPWM(self, self.step,self.dir,  frequency,step_count,dir,waveform, mode)


    def move_steps(self, step_count, delay, dir,start=None,freq=None, reverse_delays=False):
    
        if not self.GPIO_OUTPUTS:
            self.INITGPIO()
        
        if delay is None:
            delay = computeLinearDelay(step_count, freq)
        
        if not self.test:
            GPIO.setdir(dir,self.dir)
       
        for i in range(int(step_count)):

            if not self.test:
                GPIO.step_pulse(delay[i],self.step)

            sleep(delay[i])

        
           
    def move_up_down(self, dir, test=False, distance=0.1):
        #zero for up
        #moves 0.1 mm every call
        #compute the step count and freq for 1 mm in 1 mm/s
        steps = int(self.steps_per_rev*distance)
        freq = 1/2 * self.manual_speed*100 ## adjust speed

        #move it
        if not test:
            self.move_steps(steps,None, dir, freq)



    def backtozero(self, distance):
        print(distance)
        self.move_up_down(0, self.test, distance)



    ##open gpio ports
    def openPorts(self, *args, **kwargs):
        if not self.test:
            GPIO.initGPIO(args, mode=kwargs["mode"])

    def INITGPIO(self):
        self.openPorts(self.step, mode = self.gpio_mode)
        self.openPorts(self.dir,mode = self.gpio_mode)
        self.openPorts(self.m1, self.m2, self.m3,  mode = self.gpio_mode)
        if not self.test:
            GPIO.set_mode(self.mode,RESOLUTION_DICT[self.resolution][0])
            
        self.GPIO_OUTPUTS=True



    def cleanGPIO(self):
        if not self.test:
            GPIO.cleanGPIO()
        self.GPIO_OUTPUTS = False



class ForceSensor():
    def __init__(self,test=False):
        
        self.test=test
        if not self.test:
            import busio
            import board
            import adafruit_ads1x15.ads1015 as ADS
            from adafruit_ads1x15.analog_in import AnalogIn
            
            i2c = busio.I2C(board.SCL, board.SDA)
            
            self.ads = ADS.ADS1015(i2c)
            self.chan = AnalogIn(self.ads, ADS.P0)
        self.GAIN = 2 / 3
        self.set_calibration()
    def set_calibration(self):
        self.offset, self.multiplier = configreader('offset', 'multiplier',category='calibration',file="Stepper/motorconfig.cfg")
        self.offset,self.multiplier = float(self.offset), float(self.multiplier)
    
    def getreading(self):
        if self.test:

            import random
            return random.randint(0,50)

            # Read the specified ADC channel using the previously set gain value.
        reading = (self.chan.value)
            # Note you can also pass in an optional data_rate parameter that controls
            # the ADC conversion time (in samples/second). Each chip has a different
            # set of allowed data rate values, see datasheet Table 9 config register
            # DR bit values.
            # values[i] = adc.read_adc(i, gain=GAIN, data_rate=128)
            # Each value will be a 12 or 16 bit signed integer value depending on the
            # ADC (ADS1015 = 12-bit, ADS1115 = 16-bit).
        force =   (reading-self.offset)*self.multiplier
        return force




